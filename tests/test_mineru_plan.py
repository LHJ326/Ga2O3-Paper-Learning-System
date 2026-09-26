from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INSTALLATION_CHECK = PROJECT_ROOT / "docs" / "MINERU_INSTALLATION_CHECK.md"


def test_mineru_installation_check_exists() -> None:
    assert INSTALLATION_CHECK.is_file()
