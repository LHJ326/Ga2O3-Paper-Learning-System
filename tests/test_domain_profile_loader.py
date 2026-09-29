from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.domain_profiles import (
    DomainProfileAssetError,
    DomainProfileFormatError,
    DomainProfilePathError,
    load_domain_profile,
)


def write_yaml(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def build_profile(root: Path) -> Path:
    write_yaml(root / "schema.yaml", {"fields": {"material": {"type": "structured"}}})
    write_yaml(
        root / "extraction.yaml",
        {"selector": {"element_types": ["TextBlock", "Table"], "max_evidence": 30}},
    )
    write_yaml(
        root / "validation.yaml",
        {"policies": ["core_evidence"], "review_on_warning": True},
    )
    manifest = root / "profile.yaml"
    write_yaml(
        manifest,
        {
            "profile_schema_version": "1.0",
            "profile_id": "semiconductor.ga2o3.photodetector",
            "profile_version": "1.0.0",
            "schema_path": "schema.yaml",
            "extraction_rules_path": "extraction.yaml",
            "validation_rules_path": "validation.yaml",
        },
    )
    return manifest


def test_loads_versioned_profile_and_yaml_assets(tmp_path: Path) -> None:
    manifest = build_profile(tmp_path / "profile")

    profile = load_domain_profile(manifest)

    assert profile.profile_id == "semiconductor.ga2o3.photodetector"
    assert profile.version == "1.0.0"
    assert profile.profile_version == "1.0.0"
    assert profile.schema_path == manifest.parent / "schema.yaml"
    assert profile.extraction_rules_path == manifest.parent / "extraction.yaml"
    assert profile.validation_rules_path == manifest.parent / "validation.yaml"
    assert profile.schema["fields"]["material"]["type"] == "structured"
    assert profile.extraction_rules["selector"]["max_evidence"] == 30
    assert profile.validation_rules["policies"] == ("core_evidence",)
    assert len(profile.fingerprint) == 64


def test_fingerprint_is_stable_for_equivalent_yaml_key_order(tmp_path: Path) -> None:
    manifest = build_profile(tmp_path / "profile")
    first = load_domain_profile(manifest)
    write_yaml(
        manifest.parent / "schema.yaml",
        {"fields": {"material": {"type": "structured"}}},
    )

    second = load_domain_profile(manifest)

    assert first.fingerprint == second.fingerprint


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("profile_id", "Ga2O3 Profile"),
        ("profile_version", "1.0"),
        ("profile_schema_version", "2.0"),
    ],
)
def test_rejects_invalid_manifest_identity_or_version(
    tmp_path: Path, field: str, value: str
) -> None:
    manifest = build_profile(tmp_path / "profile")
    payload = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    payload[field] = value
    write_yaml(manifest, payload)

    with pytest.raises(DomainProfileFormatError):
        load_domain_profile(manifest)


def test_rejects_missing_required_manifest_field(tmp_path: Path) -> None:
    manifest = build_profile(tmp_path / "profile")
    payload = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    del payload["validation_rules_path"]
    write_yaml(manifest, payload)

    with pytest.raises(DomainProfileFormatError, match="missing required fields"):
        load_domain_profile(manifest)


def test_rejects_path_traversal_outside_profile_root(tmp_path: Path) -> None:
    root = tmp_path / "profile"
    manifest = build_profile(root)
    write_yaml(tmp_path / "outside.yaml", {"fields": {}})
    payload = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    payload["schema_path"] = "../outside.yaml"
    write_yaml(manifest, payload)

    with pytest.raises(DomainProfilePathError, match="escapes"):
        load_domain_profile(manifest)


def test_rejects_absolute_and_network_asset_paths(tmp_path: Path) -> None:
    manifest = build_profile(tmp_path / "profile")
    payload = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    payload["schema_path"] = (tmp_path / "profile" / "schema.yaml").as_posix()
    write_yaml(manifest, payload)
    with pytest.raises(DomainProfilePathError, match="relative local path"):
        load_domain_profile(manifest)

    payload["schema_path"] = "https://example.invalid/schema.yaml"
    write_yaml(manifest, payload)
    with pytest.raises(DomainProfilePathError, match="relative local path"):
        load_domain_profile(manifest)


def test_rejects_missing_or_non_mapping_assets(tmp_path: Path) -> None:
    manifest = build_profile(tmp_path / "profile")
    payload = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    payload["validation_rules_path"] = "missing.yaml"
    write_yaml(manifest, payload)
    with pytest.raises(DomainProfileAssetError, match="does not exist"):
        load_domain_profile(manifest)

    payload["validation_rules_path"] = "validation.yaml"
    write_yaml(manifest.parent / "validation.yaml", ["not", "a", "mapping"])
    write_yaml(manifest, payload)
    with pytest.raises(DomainProfileAssetError, match="must be a YAML mapping"):
        load_domain_profile(manifest)


def test_explicit_allowed_roots_support_controlled_compatibility_assets(
    tmp_path: Path,
) -> None:
    profiles = tmp_path / "profiles"
    shared = tmp_path / "shared"
    manifest = build_profile(profiles)
    write_yaml(shared / "schema.yaml", {"fields": {"shared": {"type": "structured"}}})
    payload = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    payload["schema_path"] = "../shared/schema.yaml"
    write_yaml(manifest, payload)

    profile = load_domain_profile(manifest, allowed_roots=(tmp_path,))

    assert profile.schema_path == shared / "schema.yaml"
    assert "shared" in profile.schema["fields"]
