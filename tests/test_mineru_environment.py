from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MINERU_ENVIRONMENT = PROJECT_ROOT / ".venv-mineru"
SETUP_NOTES = PROJECT_ROOT / "docs" / "MINERU_SETUP_NOTES.md"
ENVIRONMENT_RECORD = PROJECT_ROOT / "docs" / "MINERU_ENVIRONMENT_RECORD.md"
REQUIREMENTS_SNAPSHOT = PROJECT_ROOT / "requirements" / "requirements-mineru.txt"


def test_mineru_virtual_environment_path_exists() -> None:
    assert MINERU_ENVIRONMENT.is_dir()


def test_mineru_setup_notes_exist() -> None:
    assert SETUP_NOTES.is_file()


def test_mineru_environment_record_exists() -> None:
    assert ENVIRONMENT_RECORD.is_file()


def test_mineru_requirements_snapshot_exists() -> None:
    assert REQUIREMENTS_SNAPSHOT.is_file()
