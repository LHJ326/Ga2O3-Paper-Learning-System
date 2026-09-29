from pathlib import Path

import pytest
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
P001_METADATA = PROJECT_ROOT / "data" / "metadata" / "P001.yaml"


def test_p001_metadata_exists() -> None:
    assert P001_METADATA.is_file()


def test_p001_metadata_is_readable_and_registered() -> None:
    with P001_METADATA.open(encoding="utf-8") as metadata_file:
        metadata = yaml.safe_load(metadata_file)

    assert metadata["paper_id"] == "P001"
    assert metadata["pdf_checksum"] == (
        "468f0b89a752537ef06c11d979c4cd8cf3d9a84492193a5b1daa6235062f2f64"
    )
    assert metadata["processing_status"] == "completed"
    assert metadata["parser"] == {
        "name": "MinerU",
        "version": "4.0.7",
        "tier": "flash",
        "status": "completed",
    }
    assert metadata["adapter"]["version"] == "pending"
    assert metadata["schema"]["version"] == "current"


def test_p001_source_pdf_path_exists() -> None:
    with P001_METADATA.open(encoding="utf-8") as metadata_file:
        metadata = yaml.safe_load(metadata_file)

    source_pdf = PROJECT_ROOT / metadata["source_pdf"]
    if not source_pdf.is_file():
        pytest.skip("source PDF is user-provided and not included in public clones")
    assert source_pdf.is_file()
