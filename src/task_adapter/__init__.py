"""Generic bridge between Domain Profiles and extraction tasks."""

from .loader import TaskAdapterLoader, load_task_adapter
from .model import (
    TaskAdapter,
    TaskAdapterError,
    TaskAdapterLoadError,
    TaskEvidenceError,
    TaskRegistration,
    TaskRegistrationError,
    TaskRequest,
)
from .registry import TaskRegistry, build_default_task_registry

__all__ = [
    "TaskAdapter",
    "TaskAdapterError",
    "TaskAdapterLoadError",
    "TaskAdapterLoader",
    "TaskEvidenceError",
    "TaskRegistration",
    "TaskRegistrationError",
    "TaskRegistry",
    "TaskRequest",
    "build_default_task_registry",
    "load_task_adapter",
]
