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


def concept(slug: str) -> Callable[[Callable], Callable]:
    """Register the decorated callable as the detector for a knowledge concept ``slug``."""
    def deco(fn: Callable) -> Callable:
        existing = _DETECTORS.get(slug)
        if existing is not None and existing is not fn:
            raise ValueError(
                f"concept '{slug}' already registered by {existing!r}"
            )
        _DETECTORS[slug] = fn
        fn._concept_slug = slug  # type: ignore[attr-defined]
        return fn
    return deco


def detectors() -> dict[str, Callable]:
    """Return a copy of the slug -> detector mapping registered so far."""
    return dict(_DETECTORS)


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
