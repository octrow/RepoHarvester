"""docs/logic-map.md names real modules: a rename that forgets the map fails here."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT  # flat layout: Module: paths start at the repo root
MAP = ROOT / "docs" / "logic-map.md"


def _module_refs() -> list[str]:
    lines = [line for line in MAP.read_text(encoding="utf-8").splitlines() if line.startswith("Module:")]
    return [ref for line in lines for ref in re.findall(r"`([^`]+)`", line)]


def test_every_module_line_points_to_an_existing_module():
    refs = _module_refs()
    missing = [ref for ref in refs
               if not (PACKAGE / f"{ref}.py").is_file() and not (PACKAGE / ref).is_dir()]
    assert refs
    assert missing == []
