from pathlib import Path

import yaml

from src.batch import BatchPaperObjectPipeline, PaperScanner


KNOWLEDGE_FILES = (
    "summary.md", "device_parameters.yaml", "performance.yaml", "mechanism.yaml"
)


def _paper(root: Path, paper_id: str, *, metadata: bool, knowledge: bool,
           paper_object: bool = False) -> Path:
    paper = root / "data" / "papers" / paper_id
    (paper / "knowledge").mkdir(parents=True)
    if metadata:
        metadata_root = root / "data" / "metadata"
        metadata_root.mkdir(parents=True, exist_ok=True)
        (metadata_root / f"{paper_id}.yaml").write_text(
            f"paper_id: {paper_id}\n", encoding="utf-8"
        )
    if knowledge:
        for name in KNOWLEDGE_FILES:
            (paper / "knowledge" / name).write_text("{}\n", encoding="utf-8")
    if paper_object:
        (paper / "paper_object.yaml").write_text("paper_id: test\n", encoding="utf-8")
    return paper


def test_scanner_discovers_directories_and_legacy_pdfs_without_duplicates(tmp_path: Path) -> None:
    papers = tmp_path / "data" / "papers"
    (papers / "P001").mkdir(parents=True)
    (papers / "TEMPLATE").mkdir()
    (papers / "P001.pdf").write_bytes(b"pdf")
    (papers / "P002.pdf").write_bytes(b"pdf")
    (papers / "notes.pdf").write_bytes(b"pdf")
    candidates = PaperScanner(papers).scan()
    assert [item.paper_id for item in candidates] == ["P001", "P002"]
    assert candidates[0].object_dir == papers / "P001"
    assert candidates[0].source_pdf == papers / "P001.pdf"
    assert candidates[1].object_dir == papers / "P002"


def test_metadata_incomplete_skips_knowledge_stage(tmp_path: Path) -> None:
    _paper(tmp_path, "P001", metadata=False, knowledge=False)
    result = BatchPaperObjectPipeline(project_root=tmp_path).run()
    record = result.report["papers"][0]
    assert result.report["mode"] == "dry_run"
    assert record["state"] == "pending"
    assert record["reason"] == "metadata_not_ready"
    assert record["actions"] == []


def test_knowledge_incomplete_is_planned_but_never_called_by_default(tmp_path: Path) -> None:
    _paper(tmp_path, "P001", metadata=True, knowledge=False)
    result = BatchPaperObjectPipeline(project_root=tmp_path).run(dry_run=False)
    record = result.report["papers"][0]
    assert record["actions"] == ["run_knowledge_pipeline"]
    assert record["reason"] == "knowledge_executor_not_configured"
    assert not (tmp_path / "data" / "papers" / "P001" / "paper_object.yaml").exists()


def test_complete_knowledge_plans_missing_paper_object_in_dry_run(tmp_path: Path) -> None:
    _paper(tmp_path, "P001", metadata=True, knowledge=True)
    result = BatchPaperObjectPipeline(project_root=tmp_path).run()
    record = result.report["papers"][0]
    assert record["actions"] == ["build_paper_object"]
    assert record["state"] == "pending"
    assert record["reason"] == "dry_run"


def test_existing_paper_object_is_completed_and_reported(tmp_path: Path) -> None:
    _paper(tmp_path, "P001", metadata=True, knowledge=True, paper_object=True)
    report_path = tmp_path / "batch_report.yaml"
    result = BatchPaperObjectPipeline(project_root=tmp_path).run(report_path=report_path)
    saved = yaml.safe_load(report_path.read_text(encoding="utf-8"))
    assert result.report["total_papers"] == 1
    assert result.report["completed"] == 1
    assert result.report["pending"] == 0
    assert result.report["failed"] == 0
    assert saved == result.report


def test_injected_executor_can_advance_knowledge_without_model_coupling(
    tmp_path: Path, monkeypatch
) -> None:
    paper = _paper(tmp_path, "P001", metadata=True, knowledge=False)
    calls: list[str] = []

    def knowledge_executor(candidate) -> None:
        calls.append(candidate.paper_id)
        for name in KNOWLEDGE_FILES:
            (paper / "knowledge" / name).write_text("{}\n", encoding="utf-8")

    pipeline = BatchPaperObjectPipeline(
        project_root=tmp_path, knowledge_executor=knowledge_executor
    )

    def build_object(paper_id: str) -> Path:
        output = paper / "paper_object.yaml"
        output.write_text(f"paper_id: {paper_id}\n", encoding="utf-8")
        return output

    monkeypatch.setattr(pipeline, "_build_object", build_object)
    result = pipeline.run(dry_run=False)
    assert calls == ["P001"]
    assert result.report["completed"] == 1
    assert result.report["papers"][0]["actions"] == [
        "run_knowledge_pipeline", "build_paper_object"
    ]
