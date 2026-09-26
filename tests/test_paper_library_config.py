from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAPER_LIBRARY_CONFIG = PROJECT_ROOT / "configs" / "paper_library.yaml"


def test_paper_library_yaml_can_be_read() -> None:
    with PAPER_LIBRARY_CONFIG.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    paper_library = config["paper_library"]
    assert paper_library["external_source"]["path"] == "D:/杂/A科研/传感器"
    assert paper_library["internal_structure"] == {
        "papers": "data/papers",
        "metadata": "data/metadata",
        "parsed": "data/parsed",
        "benchmark": "data/benchmark",
    }
