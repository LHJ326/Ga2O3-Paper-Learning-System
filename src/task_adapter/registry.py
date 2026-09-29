"""Explicit registry of trusted extraction-task contracts."""

from __future__ import annotations

import re

from .model import TaskRegistration, TaskRegistrationError


TASK_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class TaskRegistry:
    """Register task metadata without importing executable names from YAML."""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskRegistration] = {}

    def register(self, registration: TaskRegistration) -> None:
        if not isinstance(registration, TaskRegistration):
            raise TaskRegistrationError("registration must be a TaskRegistration")
        if not TASK_ID_PATTERN.fullmatch(registration.task_id):
            raise TaskRegistrationError("task_id has an invalid format")
        if registration.task_id in self._tasks:
            raise TaskRegistrationError(f"task is already registered: {registration.task_id}")
        if not registration.artifact_key or not registration.artifact_format:
            raise TaskRegistrationError("artifact key and format are required")
        self._tasks[registration.task_id] = registration

    def get(self, task_id: str) -> TaskRegistration:
        try:
            return self._tasks[task_id]
        except KeyError as error:
            raise TaskRegistrationError(f"unknown task: {task_id}") from error

    def task_ids(self) -> tuple[str, ...]:
        return tuple(self._tasks)


BUILTIN_TASKS = (
    TaskRegistration("summary", None, "summary", "markdown", ("evidence", "summary")),
    TaskRegistration(
        "parameter", "parameters", "parameters", "yaml", ("evidence", "measurements")
    ),
    TaskRegistration(
        "performance",
        "performance",
        "performance",
        "yaml",
        ("evidence", "measurements", "performance_semantic_consistency"),
    ),
    TaskRegistration("mechanism", "mechanism", "mechanism", "yaml", ("evidence", "mechanism")),
)


def build_default_task_registry() -> TaskRegistry:
    registry = TaskRegistry()
    for registration in BUILTIN_TASKS:
        registry.register(registration)
    return registry
