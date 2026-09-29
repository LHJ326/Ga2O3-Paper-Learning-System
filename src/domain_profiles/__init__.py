"""Versioned, declarative scientific-domain profile loading."""

from .loader import DomainProfileLoader, load_domain_profile
from .model import (
    DomainProfile,
    DomainProfileAssetError,
    DomainProfileError,
    DomainProfileFormatError,
    DomainProfilePathError,
)
from .registry import (
    DomainProfileReference,
    DomainProfileRegistry,
    DomainProfileRegistryError,
)
from .selector import (
    DomainProfileSelection,
    DomainSelectionError,
    DomainTaskSelector,
    SelectedDomainTask,
)

__all__ = [
    "DomainProfile",
    "DomainProfileAssetError",
    "DomainProfileError",
    "DomainProfileFormatError",
    "DomainProfileLoader",
    "DomainProfilePathError",
    "DomainProfileReference",
    "DomainProfileRegistry",
    "DomainProfileRegistryError",
    "DomainProfileSelection",
    "DomainSelectionError",
    "DomainTaskSelector",
    "SelectedDomainTask",
    "load_domain_profile",
]
