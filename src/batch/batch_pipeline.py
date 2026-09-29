"""Dry-run-first orchestration for multiple Paper Objects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml

from src.paper_object import (
    PaperObjectBuilder,
    PaperObjectExporter,
    PaperObjectValidator,
    load_paper_object_schema,
)
from src.paper_object.schema import PROJECT_ROOT

from .scanner import PaperCandidate, PaperScanner
from .status_tracker import PaperProcessingState, PaperStatusTracker


KnowledgeExecutor = Callable[[PaperCandidate], None]


@dataclass(frozen=True)
class BatchPipelineResult:
    report_path: Path
    report: dict[str, Any]


class BatchPaperObjectPipeline:
    """Plan by default; never invokes a model unless a caller injects an executor."""

    def __init__(
        self,
        *,
        project_root: str | Path = PROJECT_ROOT,
        scanner: PaperScanner | None = None,
        status_tracker: PaperStatusTracker | None = None,
        knowledge_executor: KnowledgeExecutor | None = None,
    ) -> None:
        self.project_root = Path(project_root)
        papers_root = self.project_root / "data" / "papers"
        self.scanner = scanner or PaperScanner(papers_root)
        self.status_tracker = status_tracker or PaperStatusTracker(
            metadata_root=self.project_root / "data" / "metadata"
        )
        self.knowledge_executor = knowledge_executor

    def run(
        self,
        *,
        dry_run: bool = True,
        report_path: str | Path | None = None,
    ) -> BatchPipelineResult:
        records: list[dict[str, Any]] = []
        for candidate in self.scanner.scan():
            try:
                record = self._process(candidate, dry_run=dry_run)
            except Exception as error:
                record = {
                    "paper_id": candidate.paper_id,
                    "state": "failed",
                    "actions": [],
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
            records.append(record)
        report = {
            "mode": "dry_run" if dry_run else "execute",
            "total_papers": len(records),
            "completed": sum(item["state"] == "completed" for item in records),
            "pending": sum(item["state"] == "pending" for item in records),
            "failed": sum(item["state"] == "failed" for item in records),
            "papers": records,
        }
        output = Path(report_path) if report_path else (
            self.project_root / "data" / "papers" / "batch_report.yaml"
        )
        self._write_report(output, report)
        return BatchPipelineResult(output, report)

    def _process(self, candidate: PaperCandidate, *, dry_run: bool) -> dict[str, Any]:
        state = self.status_tracker.inspect(candidate)
        actions: list[str] = []
        if not state.metadata_ready:
            return self._record(state, "pending", actions, "metadata_not_ready")
        if not state.knowledge_ready:
            actions.append("run_knowledge_pipeline")
            if dry_run or self.knowledge_executor is None:
                reason = "dry_run" if dry_run else "knowledge_executor_not_configured"
                return self._record(state, "pending", actions, reason)
            self.knowledge_executor(candidate)
            state = self.status_tracker.inspect(candidate)
            if not state.knowledge_ready:
                return self._record(state, "pending", actions, "knowledge_still_incomplete")
        if not state.paper_object_ready:
            actions.append("build_paper_object")
            if dry_run:
                return self._record(state, "pending", actions, "dry_run")
            self._build_object(candidate.paper_id)
            state = self.status_tracker.inspect(candidate)
        return self._record(
            state,
            "completed" if state.paper_object_ready else "pending",
            actions,
            None if state.paper_object_ready else "paper_object_missing",
        )

    def _build_object(self, paper_id: str) -> Path:
        schema = load_paper_object_schema()
        payload = PaperObjectBuilder(
            project_root=self.project_root, schema=schema
        ).build(paper_id)
        return PaperObjectExporter(validator=PaperObjectValidator(schema)).export(
            payload,
            self.project_root / "data" / "papers" / paper_id / "paper_object.yaml",
        )

    @staticmethod
    def _record(
        state: PaperProcessingState,
        outcome: str,
        actions: list[str],
        reason: str | None,
    ) -> dict[str, Any]:
        return {
            "paper_id": state.paper_id,
            "state": outcome,
            "metadata_ready": state.metadata_ready,
            "knowledge_ready": state.knowledge_ready,
            "paper_object_ready": state.paper_object_ready,
            "missing_knowledge_files": list(state.missing_knowledge_files),
            "actions": actions,
            "reason": reason,
        }

    @staticmethod
    def _write_report(path: Path, report: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            yaml.safe_dump(report, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        temporary.replace(path)


def main() -> None:
    result = BatchPaperObjectPipeline().run(dry_run=True)
    print(f"Batch report: {result.report_path}")
    print(f"Total papers: {result.report['total_papers']}")
    print(f"Completed: {result.report['completed']}")
    print(f"Pending: {result.report['pending']}")
    print(f"Failed: {result.report['failed']}")


if __name__ == "__main__":
    main()
