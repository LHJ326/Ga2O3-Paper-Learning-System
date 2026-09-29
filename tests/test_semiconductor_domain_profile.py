from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.domain_profiles import load_domain_profile
from src.paper_object.builder import PaperObjectBuilder


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = PROJECT_ROOT / "data" / "domain_profiles" / "semiconductor" / "profile.yaml"
LEGACY_ROOT = PROJECT_ROOT / "data" / "domains" / "semiconductor" / "ga2o3"


def thaw(value: Any) -> Any:
    if hasattr(value, "items"):
        return {key: thaw(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [thaw(child) for child in value]
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_semiconductor_profile_loads_all_local_assets() -> None:
    profile = load_domain_profile(PROFILE_PATH)

    assert profile.profile_id == "semiconductor.ga2o3.photodetector"
    assert profile.profile_version == "1.0.0"
    assert profile.schema["domain"]["name"] == "Ga2O3 Photodetector"
    assert profile.extraction_rules["policies"]["evidence_only"] is True
    assert profile.validation_rules["policies"]["mutate_extracted_values"] is False


def test_profile_maps_every_legacy_ga2o3_schema_without_field_loss() -> None:
    schema = thaw(load_domain_profile(PROFILE_PATH).schema)
    mappings = {
        "domain": ("schema.yaml", "field_definitions"),
        "parameters": ("parameter_schema.yaml", "sections"),
        "material_device": ("material_device_schema.yaml", "sections"),
        "performance": ("performance_schema.yaml", "groups"),
        "mechanism": ("mechanism_schema.yaml", "fields"),
    }

    for profile_key, (filename, legacy_key) in mappings.items():
        legacy = load_yaml(LEGACY_ROOT / filename)
        assert schema[profile_key][legacy_key] == legacy[legacy_key]


def test_extraction_rules_preserve_v010_artifact_contract() -> None:
    profile = load_domain_profile(PROFILE_PATH)
    compatibility = thaw(profile.extraction_rules["compatibility"])

    assert compatibility["legacy_artifacts"] == PaperObjectBuilder.KNOWLEDGE_FILES
    assert compatibility["paper_object_knowledge_keys"] == list(
        PaperObjectBuilder.KNOWLEDGE_FILES
    )
    assert profile.extraction_rules["tasks"]["material_device"]["max_selected_evidence"] == 30
    assert profile.extraction_rules["tasks"]["performance"]["max_selected_evidence"] == 30
    assert profile.extraction_rules["tasks"]["mechanism"]["max_selected_evidence"] == 30


def test_validation_rules_retain_ga2o3_quality_checks() -> None:
    rules = load_domain_profile(PROFILE_PATH).validation_rules

    assert "Device Structure" in rules["summary"]["required_sections"]
    assert rules["measurements"]["numeric_values_require_unit"] is True
    assert set(rules["performance_semantic_consistency"]["fields"]) == {
        "on_off_ratio", "responsivity", "detectivity", "response_time"
    }
    assert rules["performance_semantic_consistency"]["preserve_original_result"] is True


def test_profile_keeps_paper_object_v010_knowledge_shape() -> None:
    profile = load_domain_profile(PROFILE_PATH)
    paper_object_schema = load_yaml(PROJECT_ROOT / "data" / "paper_object" / "schema.yaml")

    assert tuple(profile.schema["compatibility"]["knowledge_keys"]) == tuple(
        paper_object_schema["sections"]["knowledge"]["required"]
    )
    assert tuple(profile.schema["compatibility"]["knowledge_keys"]) == tuple(
        PaperObjectBuilder.KNOWLEDGE_FILES
    )
