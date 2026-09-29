"""Repository-owned registry for exact Domain Profile versions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

import yaml

from .loader import PROFILE_ID_PATTERN, SEMANTIC_VERSION_PATTERN, load_domain_profile
from .model import DomainProfile


class DomainProfileRegistryError(ValueError):
    """Raised when a profile catalog is invalid or cannot resolve a profile."""


@dataclass(frozen=True, slots=True)
class DomainProfileReference:
    profile_id: str
    profile_version: str
    manifest_path: Path
    status: str


class DomainProfileRegistry:
    """Load and resolve an approved catalog without implicit defaults."""

    CATALOG_VERSION = "1.0"
    STATUSES = frozenset({"experimental", "stable", "deprecated"})

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).resolve()
        self._references = self._load()

    def references(self) -> tuple[DomainProfileReference, ...]:
        return tuple(self._references.values())

    def resolve(self, profile_id: str, profile_version: str) -> DomainProfileReference:
        try:
            return self._references[(profile_id, profile_version)]
        except KeyError as error:
            raise DomainProfileRegistryError(
                f"Domain Profile is not registered: {profile_id}@{profile_version}"
            ) from error

    def load_profile(self, profile_id: str, profile_version: str) -> DomainProfile:
        reference = self.resolve(profile_id, profile_version)
        profile = load_domain_profile(reference.manifest_path)
        if profile.profile_id != profile_id or profile.profile_version != profile_version:
            raise DomainProfileRegistryError(
                "catalog identity/version does not match the loaded profile manifest"
            )
        return profile

    def _load(self) -> dict[tuple[str, str], DomainProfileReference]:
        if not self.path.is_file():
            raise FileNotFoundError(f"Domain Profile catalog does not exist: {self.path}")
        try:
            payload = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as error:
            raise DomainProfileRegistryError("cannot read Domain Profile catalog") from error
        if not isinstance(payload, Mapping):
            raise DomainProfileRegistryError("Domain Profile catalog must be a mapping")
        if payload.get("catalog_version") != self.CATALOG_VERSION:
            raise DomainProfileRegistryError(
                f"catalog_version must be {self.CATALOG_VERSION}"
            )
        entries = payload.get("profiles")
        if not isinstance(entries, list):
            raise DomainProfileRegistryError("profiles must be a list")

        references: dict[tuple[str, str], DomainProfileReference] = {}
        for index, entry in enumerate(entries):
            reference = self._validate_entry(entry, index)
            key = (reference.profile_id, reference.profile_version)
            if key in references:
                raise DomainProfileRegistryError(
                    f"duplicate Domain Profile registration: {key[0]}@{key[1]}"
                )
            references[key] = reference
        return references

    def _validate_entry(self, entry: Any, index: int) -> DomainProfileReference:
        if not isinstance(entry, Mapping):
            raise DomainProfileRegistryError(f"profiles[{index}] must be a mapping")
        required = ("profile_id", "profile_version", "manifest_path", "status")
        missing = [field for field in required if field not in entry]
        if missing:
            raise DomainProfileRegistryError(f"profiles[{index}] is missing fields: {missing}")
        profile_id = entry["profile_id"]
        version = entry["profile_version"]
        raw_path = entry["manifest_path"]
        status = entry["status"]
        if not isinstance(profile_id, str) or not PROFILE_ID_PATTERN.fullmatch(profile_id):
            raise DomainProfileRegistryError(f"profiles[{index}].profile_id is invalid")
        if not isinstance(version, str) or not SEMANTIC_VERSION_PATTERN.fullmatch(version):
            raise DomainProfileRegistryError(f"profiles[{index}].profile_version is invalid")
        if status not in self.STATUSES:
            raise DomainProfileRegistryError(f"profiles[{index}].status is invalid")
        if not isinstance(raw_path, str) or not raw_path:
            raise DomainProfileRegistryError(f"profiles[{index}].manifest_path is invalid")
        relative = Path(raw_path)
        split = urlsplit(raw_path)
        if split.scheme or split.netloc or relative.is_absolute():
            raise DomainProfileRegistryError("manifest_path must be a relative local path")
        manifest = (self.path.parent / relative).resolve()
        root = self.path.parent.resolve()
        if manifest != root and not manifest.is_relative_to(root):
            raise DomainProfileRegistryError("manifest_path escapes the catalog root")
        if manifest.suffix.casefold() not in {".yaml", ".yml"} or not manifest.is_file():
            raise DomainProfileRegistryError(f"profile manifest does not exist: {manifest}")
        return DomainProfileReference(profile_id, version, manifest, status)
