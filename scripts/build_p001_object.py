"""Build and validate the finalized P001 Paper Object."""
from src.paper_object import (PaperObjectBuilder, PaperObjectExporter,
                              PaperObjectValidator, load_paper_object_schema)
from src.paper_object.schema import PROJECT_ROOT

def main() -> None:
    schema = load_paper_object_schema()
    payload = PaperObjectBuilder(project_root=PROJECT_ROOT, schema=schema).build("P001")
    output = PaperObjectExporter(validator=PaperObjectValidator(schema)).export(
        payload, PROJECT_ROOT / "data" / "papers" / "P001" / "paper_object.yaml"
    )
    print(f"Paper Object: {output}")
    print(f"Evidence records: {len(payload['source']['evidence_index'])}")
    print(f"Evidence coverage: {payload['validation']['evidence_coverage']:.1%}")
    print(f"Review status: {payload['validation']['review_status']}")
    print(f"Warnings: {len(payload['validation']['warnings'])}")

if __name__ == "__main__":
    main()
