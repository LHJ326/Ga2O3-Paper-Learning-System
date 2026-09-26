from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_CONFIG = PROJECT_ROOT / "configs" / "tools.yaml"


def test_tools_yaml_can_be_read() -> None:
    with TOOLS_CONFIG.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    tools = config["tools"]
    assert set(tools) == {"pdf_parser", "ocr", "translation", "rag"}
    assert tools["pdf_parser"]["candidates"] == ["MinerU", "Docling", "Marker"]
    assert "selected_for_testing" in tools["pdf_parser"]
    assert tools["pdf_parser"]["selected_for_testing"] == {
        "name": "MinerU",
        "status": "testing",
    }
    assert all(
        tools[tool_name]["status"] == "candidate"
        for tool_name in ("ocr", "translation", "rag")
    )
