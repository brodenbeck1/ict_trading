"""
Concept Lineage — Mermaid diagram generator.

Usage:
    python scripts/lineage.py                  # print full diagram
    python scripts/lineage.py model-2022       # print one model's transitive graph
    python scripts/lineage.py --update-readme  # regenerate the README section
"""

import sys
import pathlib

# ensure the package is importable when run from the repo root
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import ict  # noqa: F401  (populates the registry via side-effect imports)
from ict import registry

_README = pathlib.Path(__file__).resolve().parents[1] / "README.md"
_START  = "<!-- lineage-start -->"
_END    = "<!-- lineage-end -->"


def _diagram(slug: str | None = None) -> str:
    return "```mermaid\n" + registry.mermaid(slug) + "\n```"


def _update_readme(diagram: str) -> None:
    text = _README.read_text()
    if _START not in text or _END not in text:
        print(f"README missing sentinel comments {_START!r} / {_END!r}", file=sys.stderr)
        sys.exit(1)
    before = text[: text.index(_START) + len(_START)]
    after  = text[text.index(_END):]
    _README.write_text(before + "\n" + diagram + "\n" + after)
    print(f"README updated: {_README}")


def main() -> None:
    args = sys.argv[1:]

    if "--update-readme" in args:
        args = [a for a in args if a != "--update-readme"]
        slug = args[0] if args else None
        _update_readme(_diagram(slug))
    elif args:
        print(_diagram(args[0]))
    else:
        print(_diagram())


if __name__ == "__main__":
    main()
