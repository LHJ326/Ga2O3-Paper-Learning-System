"""Safe YAML loader for versioned Domain Profiles."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlsplit

import yaml

from .model import (
    DomainProfile,
    DomainProfileAssetError,
    DomainProfileFormatError,
    DomainProfilePathError,
    freeze_mapping,
)


PROFILE_SCHEMA_VERSION = "1.0"
PROFILE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
SEMANTIC_VERSION_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
REQUIRED_FIELDS = (
    "profile_schema_version",
    "profile_id",
    "profile_version",
    "schema_path",
    "extraction_rules_path",
    "validation_rules_path",
)
ASSET_FIELDS = (
    "schema_path",
    "extraction_rules_path",
    "validation_rules_path",
)
YAML_SUFFIXES = frozenset({".yaml", ".yml"})


class DomainProfileLoader:
    """Load a profile without executing code or resolving network resources.

    By default, every referenced asset must remain beneath the manifest's
    directory. Callers may provide additional repository-owned roots for a
    controlled compatibility migration.
    """

    def __init__(self, *, allowed_roots: Iterable[str | Path] | None = None) -> None:
        self._configured_roots = (
            tuple(Path(root).resolve() for root in allowed_roots)
            if allowed_roots is not None
            else None
        )

    def load(self, path: str | Path) -> DomainProfile:
        source = Path(path).resolve()
        manifest = self._load_yaml_mapping(source, kind="profile manifest")
        self._validate_manifest(manifest)

        allowed_roots = self._allowed_roots(source)
        resolved = {
            field: self._resolve_asset(
                source=source,
                raw_path=manifest[field],
                field=field,
                allowed_roots=allowed_roots,
            )
            for field in ASSET_FIELDS
        }
        schema = self._load_yaml_mapping(resolved["schema_path"], kind="schema asset")
        extraction = self._load_yaml_mapping(
            resolved["extraction_rules_path"], kind="extraction rules asset"
        )
        validation = self._load_yaml_mapping(
            resolved["validation_rules_path"], kind="validation rules asset"
        )
        fingerprint = self._fingerprint(manifest, schema, extraction, validation)

        return DomainProfile(
            profile_schema_version=manifest["profile_schema_version"],
            profile_id=manifest["profile_id"],
            version=manifest["profile_version"],
            source_path=source,
            schema_path=resolved["schema_path"],
            extraction_rules_path=resolved["extraction_rules_path"],
            validation_rules_path=resolved["validation_rules_path"],
            schema=freeze_mapping(schema),
            extraction_rules=freeze_mapping(extraction),
            validation_rules=freeze_mapping(validation),
            fingerprint=fingerprint,
        )

    def _allowed_roots(self, source: Path) -> tuple[Path, ...]:
        roots = self._configured_roots or (source.parent.resolve(),)
        if self._configured_roots is not None and not self._inside_any(source, roots):
            raise DomainProfilePathError(
                f"profile manifest is outside the approved roots: {source}"
            )
        return roots

    @staticmethod
    def _validate_manifest(manifest: Mapping[str, Any]) -> None:
        missing = [field for field in REQUIRED_FIELDS if field not in manifest]
        if missing:
            raise DomainProfileFormatError(
                f"profile manifest is missing required fields: {missing}"
            )
        if manifest["profile_schema_version"] != PROFILE_SCHEMA_VERSION:
            raise DomainProfileFormatError(
                f"profile_schema_version must be {PROFILE_SCHEMA_VERSION}"
            )
        profile_id = manifest["profile_id"]
        if not isinstance(profile_id, str) or not PROFILE_ID_PATTERN.fullmatch(profile_id):
            raise DomainProfileFormatError("profile_id has an invalid format")
        version = manifest["profile_version"]
        if not isinstance(version, str) or not SEMANTIC_VERSION_PATTERN.fullmatch(version):
            raise DomainProfileFormatError("profile_version must be a semantic version")
        for field in ASSET_FIELDS:
            value = manifest[field]
            if not isinstance(value, str) or not value.strip():
                raise DomainProfileFormatError(f"{field} must be a non-empty string")

    @classmethod
    def _resolve_asset(
        cls,
        *,
        source: Path,
        raw_path: str,
        field: str,
        allowed_roots: tuple[Path, ...],
    ) -> Path:
        split = urlsplit(raw_path)
        relative = Path(raw_path)
        if split.scheme or split.netloc or relative.is_absolute():
            raise DomainProfilePathError(f"{field} must be a relative local path")
        candidate = (source.parent / relative).resolve()
        if not cls._inside_any(candidate, allowed_roots):
            raise DomainProfilePathError(f"{field} escapes the approved profile roots")
        if candidate.suffix.casefold() not in YAML_SUFFIXES:
            raise DomainProfilePathError(f"{field} must reference a YAML file")
        if not candidate.is_file():
            raise DomainProfileAssetError(f"{field} does not exist: {candidate}")
        return candidate

    @staticmethod
    def _inside_any(path: Path, roots: tuple[Path, ...]) -> bool:
        return any(path == root or path.is_relative_to(root) for root in roots)

    @staticmethod
    def _load_yaml_mapping(path: Path, *, kind: str) -> dict[str, Any]:
        if path.suffix.casefold() not in YAML_SUFFIXES:
            raise DomainProfilePathError(f"{kind} must be a YAML file: {path}")
        if not path.is_file():
            raise DomainProfileAssetError(f"{kind} does not exist: {path}")
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as error:
            raise DomainProfileAssetError(f"cannot load {kind}: {path}") from error
        if not isinstance(payload, dict):
            raise DomainProfileAssetError(f"{kind} must be a YAML mapping: {path}")
        return payload

    @staticmethod
    def _fingerprint(*payloads: Mapping[str, Any]) -> str:
        canonical = json.dumps(
            payloads,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_domain_profile(
    path: str | Path,
    *,
    allowed_roots: Iterable[str | Path] | None = None,
) -> DomainProfile:
    """Convenience entry point for one profile manifest."""

    return DomainProfileLoader(allowed_roots=allowed_roots).load(path)
