from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.domain_profiles import (
    DomainProfileRegistry,
    DomainProfileRegistryError,
    DomainProfileSelection,
    DomainSelectionError,
    DomainTaskSelector,
)
from src.paper_object.builder import PaperObjectBuilder
from src.registry import RegistryManager


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = PROJECT_ROOT / "data" / "domain_profiles" / "catalog.yaml"
PROFILE_ID = "semiconductor.ga2o3.photodetector"
PROFILE_VERSION = "1.0.0"
EXPLICIT = DomainProfileSelection(PROFILE_ID, PROFILE_VERSION)


@pytest.fixture(scope="module")
def domain_registry() -> DomainProfileRegistry:
    return DomainProfileRegistry(CATALOG_PATH)


def test_domain_registry_resolves_exact_registered_version(domain_registry) -> None:
    reference = domain_registry.resolve(PROFILE_ID, PROFILE_VERSION)
    profile = domain_registry.load_profile(PROFILE_ID, PROFILE_VERSION)

    assert reference.status == "stable"
    assert reference.manifest_path.name == "profile.yaml"
    assert profile.profile_id == PROFILE_ID
    assert profile.profile_version == PROFILE_VERSION
    with pytest.raises(DomainProfileRegistryError, match="not registered"):
        domain_registry.resolve(PROFILE_ID, "1.0.1")


def test_explicit_configuration_has_priority_over_registry(domain_registry) -> None:
    selector = DomainTaskSelector(domain_registry)
    paper_record = {
        "paper_id": "P001",
        "domain_profile": {
            "profile_id": "unregistered.domain",
            "profile_version": "9.9.9",
        },
    }

    selected = selector.select("summary", explicit=EXPLICIT, paper_record=paper_record)

    assert selected.source == "explicit"
    assert selected.profile.profile_id == PROFILE_ID


def test_registry_selection_is_used_when_explicit_value_is_absent(domain_registry) -> None:
    selector = DomainTaskSelector(domain_registry)
    selected = selector.select(
        "parameter",
        paper_record={
            "paper_id": "P002",
            "domain_profile": {
                "profile_id": PROFILE_ID,
                "profile_version": PROFILE_VERSION,
            },
        },
    )

    assert selected.source == "registry"
    assert selected.adapter.task_id == "parameter"
    assert selected.adapter.artifact_path == "device_parameters.yaml"


def test_selector_never_guesses_domain_from_paper_content(domain_registry) -> None:
    selector = DomainTaskSelector(domain_registry)
    paper_record = {
        "paper_id": "P999",
        "title": "A beta-Ga2O3 semiconductor photodetector",
        "abstract": "Ga2O3 device performance and mechanism",
    }

    with pytest.raises(DomainSelectionError, match="implicit fallback is disabled"):
        selector.select("summary", paper_record=paper_record)


@pytest.mark.parametrize(
    "configured",
    [
        {},
        {"profile_id": PROFILE_ID},
        {"profile_version": PROFILE_VERSION},
    ],
)
def test_selector_rejects_incomplete_explicit_configuration(
    domain_registry, configured
) -> None:
    selector = DomainTaskSelector(domain_registry)

    with pytest.raises(DomainSelectionError):
        selector.select("summary", explicit=configured)


@pytest.mark.parametrize("task_id", ["summary", "parameter", "performance", "mechanism"])
def test_selector_integrates_registered_tasks(domain_registry, task_id: str) -> None:
    selected = DomainTaskSelector(domain_registry).select(task_id, explicit=EXPLICIT)

    assert selected.adapter.task_id == task_id
    assert selected.adapter.profile_id == PROFILE_ID
    assert selected.adapter.evidence_only is True
    assert selected.adapter.prohibit_external_knowledge is True
    assert selected.adapter.unknown_value is None


def test_catalog_rejects_duplicate_registration(tmp_path: Path) -> None:
    manifest = tmp_path / "profile.yaml"
    manifest.write_text("profile_schema_version: '1.0'\n", encoding="utf-8")
    entry = {
        "profile_id": PROFILE_ID,
        "profile_version": PROFILE_VERSION,
        "manifest_path": "profile.yaml",
        "status": "stable",
    }
    catalog = tmp_path / "catalog.yaml"
    catalog.write_text(
        yaml.safe_dump({"catalog_version": "1.0", "profiles": [entry, entry]}),
        encoding="utf-8",
    )

    with pytest.raises(DomainProfileRegistryError, match="duplicate"):
        DomainProfileRegistry(catalog)


def test_catalog_rejects_path_traversal(tmp_path: Path) -> None:
    outside = tmp_path / "outside.yaml"
    outside.write_text("profile_schema_version: '1.0'\n", encoding="utf-8")
    root = tmp_path / "catalog"
    root.mkdir()
    catalog = root / "catalog.yaml"
    catalog.write_text(
        yaml.safe_dump(
            {
                "catalog_version": "1.0",
                "profiles": [{
                    "profile_id": PROFILE_ID,
                    "profile_version": PROFILE_VERSION,
                    "manifest_path": "../outside.yaml",
                    "status": "stable",
                }],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(DomainProfileRegistryError, match="escapes"):
        DomainProfileRegistry(catalog)


def test_current_p001_requires_explicit_selection_without_changing_outputs(
    domain_registry,
) -> None:
    selector = DomainTaskSelector(domain_registry)
    manager = RegistryManager(PROJECT_ROOT / "data" / "papers" / "registry.yaml")

    with pytest.raises(DomainSelectionError, match="implicit fallback is disabled"):
        selector.select_for_paper(manager, "P001", "summary")

    selected = {
        task_id: selector.select_for_paper(
            manager, "P001", task_id, explicit=EXPLICIT
        ).adapter
        for task_id in ("summary", "parameter", "performance", "mechanism")
    }
    assert {
        adapter.artifact_key: adapter.artifact_path for adapter in selected.values()
    } == PaperObjectBuilder.KNOWLEDGE_FILES
