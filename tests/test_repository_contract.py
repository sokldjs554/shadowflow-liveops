from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_repository_has_no_open_source_license_claim() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").exists() else ""
    assert "MIT" not in readme
    assert not any(ROOT.glob("LICENSE*"))


def test_ai_coding_tool_contracts_exist() -> None:
    assert (ROOT / "CLAUDE.md").exists()
    assert (ROOT / "AGENTS.md").exists()
    assert (ROOT / ".cursor" / "rules" / "shadowflow.mdc").exists()
