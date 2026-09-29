"""Data contracts and errors for Domain Profiles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


class DomainProfileError(ValueError):
    """Base error for an invalid or unreadable Domain Profile."""


class DomainProfileFormatError(DomainProfileError):
    """Raised when a profile manifest has an invalid data contract."""


class DomainProfilePathError(DomainProfileError):
    """Raised when a profile references an unsafe path."""


class DomainProfileAssetError(DomainProfileError):
    """Raised when a referenced profile asset is missing or malformed."""


def freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return a recursively immutable view of YAML-compatible data."""

    def freeze(item: Any) -> Any:
        if isinstance(item, dict):
            return MappingProxyType({str(key): freeze(child) for key, child in item.items()})
        if isinstance(item, list):
            return tuple(freeze(child) for child in item)
        return item

    return freeze(dict(value))


@dataclass(frozen=True, slots=True)
class DomainProfile:
    """A validated profile and its loaded declarative assets."""

    profile_schema_version: str
    profile_id: str
    version: str
    source_path: Path
    schema_path: Path
    extraction_rules_path: Path
    validation_rules_path: Path
    schema: Mapping[str, Any]
    extraction_rules: Mapping[str, Any]
    validation_rules: Mapping[str, Any]
    fingerprint: str

    @property
    def profile_version(self) -> str:
        """Expose the manifest term without duplicating stored state."""

        return self.version
