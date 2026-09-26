from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVALUATION_CONFIG = PROJECT_ROOT / "configs" / "evaluation.yaml"


def test_evaluation_yaml_can_be_read() -> None:
    with EVALUATION_CONFIG.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    assert config["benchmark"]["B01"] == {
        "expected_figures": 4,
        "expected_subfigures": 14,
        "expected_equations": 7,
    }
