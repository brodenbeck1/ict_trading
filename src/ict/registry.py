"""
Concept Registry
================

Binds the markdown semantic layer in ``knowledge/`` to code detectors.

Every concept file (``knowledge/<author>/<category>/<slug>.md``) carries YAML
frontmatter with a ``name`` (slug), a ``detection`` flag
(``implemented`` | ``partial`` | ``not-implemented``), and a ``parameters`` block.

Code detectors register against a slug with the :func:`concept` decorator::

    from ict.registry import concept

    @concept("fair-value-gap")
    def find_fvgs(df, ...): ...

Pass ``depends_on`` to declare what other slugs this detector composes::

    @concept("daily-bias", depends_on=["draw-on-liquidity", "premium-discount"])
    def daily_bias(df): ...

``tests/test_registry_coverage.py`` then enforces that the flags and the code
agree, so the ``detection:`` flags can never silently lie, and the
``parameters:`` blocks stay the single source of default config.
"""
from __future__ import annotations

import pathlib
from typing import Callable

import frontmatter

# src/ict/registry.py  ->  repo root is two parents up from the package dir
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_KNOWLEDGE_DIR = _REPO_ROOT / "knowledge"

_DETECTORS: dict[str, Callable] = {}
_DEPS: dict[str, list[str]] = {}
_LAYERS: dict[str, str] = {}   # slug -> 'concept' | 'intermediate' | 'model'


def concept(slug: str, depends_on: list[str] | None = None) -> Callable[[Callable], Callable]:
    """Register the decorated callable as the detector for a knowledge concept ``slug``.

    Args:
        slug:       Concept slug matching the ``name:`` in its knowledge file.
        depends_on: Slugs of other concepts/models this one composes.  Used to
                    build the lineage graph (see :func:`lineage`, :func:`mermaid`).
    """
    def deco(fn: Callable) -> Callable:
        existing = _DETECTORS.get(slug)
        if existing is not None and existing is not fn:
            raise ValueError(
                f"concept '{slug}' already registered by {existing!r}"
            )
        _DETECTORS[slug] = fn
        fn._concept_slug = slug  # type: ignore[attr-defined]
        _DEPS[slug] = list(depends_on or [])

        mod = getattr(fn, '__module__', '') or ''
        if 'models.intermediate' in mod:
            _LAYERS[slug] = 'intermediate'
        elif 'models.' in mod:
            _LAYERS[slug] = 'model'
        else:
            _LAYERS[slug] = 'concept'

        return fn
    return deco


def detectors() -> dict[str, Callable]:
    """Return a copy of the slug -> detector mapping registered so far."""
    return dict(_DETECTORS)


def lineage(slug: str) -> dict:
    """Return the transitive dependency tree for *slug*.

    Example::

        registry.lineage("daily-bias")
        # {'daily-bias': {'draw-on-liquidity': {'swing-points': {}},
        #                  'premium-discount': {},
        #                  'ohlc-candle-profiles': {}}}
    """
    visited: set[str] = set()

    def _walk(s: str) -> dict:
        if s in visited:
            return {}
        visited.add(s)
        return {d: _walk(d) for d in _DEPS.get(s, [])}

    return {slug: _walk(slug)}


def mermaid(slug: str | None = None) -> str:
    """Generate a Mermaid ``flowchart LR`` diagram of concept dependencies.

    Args:
        slug: If given, restrict the diagram to that slug's transitive graph.
              If ``None``, show all registered concepts.

    Returns:
        A Mermaid-formatted string ready to embed in a markdown code fence.
    """
    if slug:
        nodes = _collect_transitive(slug)
    else:
        nodes = set(_DETECTORS.keys())

    by_layer: dict[str, list[str]] = {'concept': [], 'intermediate': [], 'model': []}
    for s in sorted(nodes):
        layer = _LAYERS.get(s, 'concept')
        by_layer[layer].append(s)

    lines = ['flowchart LR']

    layer_labels = [('concept', 'Concepts'), ('intermediate', 'Intermediate'), ('model', 'Models')]
    for layer_key, layer_label in layer_labels:
        slugs = by_layer[layer_key]
        if not slugs:
            continue
        lines.append(f'    subgraph {layer_label}')
        for s in slugs:
            nid = _node_id(s)
            lines.append(f'        {nid}["{s}"]')
        lines.append('    end')

    lines.append('')
    for s in sorted(nodes):
        for dep in _DEPS.get(s, []):
            if dep in nodes:
                lines.append(f'    {_node_id(dep)} --> {_node_id(s)}')

    return '\n'.join(lines)


def _collect_transitive(slug: str, _seen: set[str] | None = None) -> set[str]:
    seen = _seen if _seen is not None else set()
    if slug in seen:
        return seen
    seen.add(slug)
    for dep in _DEPS.get(slug, []):
        _collect_transitive(dep, seen)
    return seen


def _node_id(slug: str) -> str:
    return slug.replace('-', '_')


def load_concepts(knowledge_dir: pathlib.Path | str | None = None) -> dict[str, dict]:
    """Parse every concept file's frontmatter into ``{slug: metadata}``.

    READMEs are skipped. ``metadata['_path']`` is the file path relative to the
    repo root, for diagnostics.
    """
    root = pathlib.Path(knowledge_dir) if knowledge_dir else _KNOWLEDGE_DIR
    out: dict[str, dict] = {}
    for md in sorted(root.rglob("*.md")):
        if md.name == "README.md":
            continue
        meta = dict(frontmatter.load(md).metadata)
        name = meta.get("name")
        if not name:
            continue
        meta["_path"] = str(md.relative_to(_REPO_ROOT))
        out[name] = meta
    return out


def params(slug: str) -> dict:
    """Default parameters for a concept, taken from its knowledge frontmatter."""
    return load_concepts().get(slug, {}).get("parameters") or {}
