from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_CONFIG = PROJECT_ROOT / "configs" / "tools.yaml"


def test_pdf_parser_candidate_configuration_exists() -> None:
    with TOOLS_CONFIG.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    pdf_parser = config["tools"]["pdf_parser"]
    assert pdf_parser["candidates"] == ["MinerU", "Docling", "Marker"]
    assert pdf_parser["selected_for_testing"]["name"] in pdf_parser["candidates"]
    assert pdf_parser["selected_for_testing"]["status"] == "testing"
