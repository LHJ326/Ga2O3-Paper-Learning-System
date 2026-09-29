from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.domain_profiles import load_domain_profile
from src.paper_object.builder import PaperObjectBuilder
from src.task_adapter import (
    TaskAdapterLoadError,
    TaskAdapterLoader,
    TaskEvidenceError,
    TaskRegistration,
    TaskRegistrationError,
    TaskRegistry,
    build_default_task_registry,
    load_task_adapter,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = PROJECT_ROOT / "data" / "domain_profiles" / "semiconductor" / "profile.yaml"


def thaw(value):
    if hasattr(value, "items"):
        return {key: thaw(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [thaw(child) for child in value]
    return value


@pytest.fixture(scope="module")
def profile():
    return load_domain_profile(PROFILE_PATH)


def test_default_registry_supports_required_tasks() -> None:
    registry = build_default_task_registry()

    assert registry.task_ids() == ("summary", "parameter", "performance", "mechanism")


def test_registry_rejects_duplicates_and_unknown_tasks() -> None:
    registry = TaskRegistry()
    registration = TaskRegistration("summary", None, "summary", "markdown", ())
    registry.register(registration)

    with pytest.raises(TaskRegistrationError, match="already registered"):
        registry.register(registration)
    with pytest.raises(TaskRegistrationError, match="unknown task"):
        registry.get("missing")


@pytest.mark.parametrize(
    ("task_id", "artifact_key", "artifact_path", "schema_key"),
    [
        ("summary", "summary", "summary.md", "required_sections"),
        ("parameter", "parameters", "device_parameters.yaml", "sections"),
        ("performance", "performance", "performance.yaml", "groups"),
        ("mechanism", "mechanism", "mechanism.yaml", "fields"),
    ],
)
def test_loader_resolves_profile_task_contract(
    profile, task_id: str, artifact_key: str, artifact_path: str, schema_key: str
) -> None:
    adapter = load_task_adapter(profile, task_id)

    assert adapter.task_id == task_id
    assert adapter.artifact_key == artifact_key
    assert adapter.artifact_path == artifact_path
    assert schema_key in adapter.output_schema
    assert len(adapter.adapter_fingerprint) == 64


def test_adapter_enforces_evidence_only_and_null_policy(profile) -> None:
    for task_id in build_default_task_registry().task_ids():
        adapter = load_task_adapter(profile, task_id)
        assert adapter.evidence_only is True
        assert adapter.prohibit_external_knowledge is True
        assert adapter.unknown_value is None


def test_bind_evidence_preserves_all_traceability_fields(profile) -> None:
    adapter = load_task_adapter(profile, "parameter")
    source = {
        "evidence_id": "E00001",
        "page": 2,
        "element_id": "text-1",
        "element_type": "TextBlock",
        "source_type": "TextBlock",
        "source_reference": "pages[1].elements[0]",
        "quote": "The device uses beta-Ga2O3.",
        "bbox": [1, 2, 3, 4],
    }

    request = adapter.bind_evidence([source])

    assert thaw(request.evidence[0]) == source
    assert request.evidence[0]["source_reference"] == source["source_reference"]
    assert tuple(request.evidence[0]["bbox"]) == tuple(source["bbox"])
    with pytest.raises(TypeError):
        request.evidence[0]["page"] = 3


@pytest.mark.parametrize(
    "evidence",
    [
        {"page": 1},
        {"evidence_id": "E00001", "page": 0},
        {"evidence_id": "E00001", "page": True},
    ],
)
def test_bind_evidence_rejects_untraceable_records(profile, evidence) -> None:
    adapter = load_task_adapter(profile, "summary")

    with pytest.raises(TaskEvidenceError):
        adapter.bind_evidence([evidence])


def test_bind_evidence_rejects_duplicate_ids(profile) -> None:
    adapter = load_task_adapter(profile, "mechanism")
    evidence = {"evidence_id": "E00001", "page": 1}

    with pytest.raises(TaskEvidenceError, match="duplicate"):
        adapter.bind_evidence([evidence, evidence])


def test_bind_evidence_rejects_unsupported_empty_input(profile) -> None:
    adapter = load_task_adapter(profile, "summary")

    with pytest.raises(TaskEvidenceError, match="at least one Evidence"):
        adapter.bind_evidence([])


def test_loader_rejects_mismatched_profile_assets(profile) -> None:
    mismatched = replace(profile, schema={**profile.schema, "profile_id": "other.domain"})

    with pytest.raises(TaskAdapterLoadError, match="does not match"):
        TaskAdapterLoader().load(mismatched, "summary")


def test_custom_task_registration_requires_profile_mapping(profile) -> None:
    registry = TaskRegistry()
    registry.register(TaskRegistration("custom", "domain", "custom", "yaml", ("evidence",)))

    with pytest.raises(TaskAdapterLoadError, match="profile mapping is missing"):
        TaskAdapterLoader(registry).load(profile, "custom")


def test_p001_v010_artifact_contract_is_unchanged(profile) -> None:
    adapters = {
        task_id: load_task_adapter(profile, task_id)
        for task_id in build_default_task_registry().task_ids()
    }

    assert {
        adapter.artifact_key: adapter.artifact_path for adapter in adapters.values()
    } == PaperObjectBuilder.KNOWLEDGE_FILES
