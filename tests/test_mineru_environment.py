from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MINERU_ENVIRONMENT = PROJECT_ROOT / ".venv-mineru"
SETUP_NOTES = PROJECT_ROOT / "docs" / "MINERU_SETUP_NOTES.md"


def test_mineru_virtual_environment_path_exists() -> None:
    assert MINERU_ENVIRONMENT.is_dir()


def test_mineru_setup_notes_exist() -> None:
    assert SETUP_NOTES.is_file()
