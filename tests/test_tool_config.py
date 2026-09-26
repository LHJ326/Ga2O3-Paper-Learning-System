from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_CONFIG = PROJECT_ROOT / "configs" / "tools.yaml"


def test_tools_yaml_can_be_read() -> None:
    with TOOLS_CONFIG.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    assert "tools" in config
    assert set(config["tools"]) == {"pdf_parser", "ocr", "translation", "rag"}
    assert all(
        tool_config["status"] == "candidate"
        for tool_config in config["tools"].values()
    )
