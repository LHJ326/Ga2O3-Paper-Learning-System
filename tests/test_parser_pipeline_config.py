from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARSER_PIPELINE_CONFIG = PROJECT_ROOT / "configs" / "parser_pipeline.yaml"


def test_parser_pipeline_yaml_can_be_read() -> None:
    with PARSER_PIPELINE_CONFIG.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    pipeline = config["pipeline"]
    assert pipeline["raw_output"]["root"] == "data/parsed"
    assert pipeline["document_output"]["root"] == "data/parsed"
    assert pipeline["parser"] == {"name": "MinerU", "version": "4.0.7"}
    assert pipeline["adapter"]["version"] == "planned"
