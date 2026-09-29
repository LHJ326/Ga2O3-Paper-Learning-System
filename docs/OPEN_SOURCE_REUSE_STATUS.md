# Open Source Reuse Status

## RAG-Anything

Source:

`<EXTERNAL_RESEARCH_ROOT>\RAG-Anything`

Status:

`ADOPT CANDIDATE`

This is an architectural candidate, not a final adoption decision. The source was downloaded and extracted manually by the user. Do not clone/download it again and do not modify the external source from this project.

## Confirmed

- Python >= 3.10
- MIT License
- LightRAG backend
- Parser support for MinerU, Docling, and PaddleOCR
- Direct pre-parsed content insertion through `insert_content_list()`
- Multimodal `content_list` items: text, image, table, equation
- Custom `doc_id`
- 0-based `page_idx`
- Absolute `img_path` requirement
- `image_caption`
- `table_caption`
- `latex`

Observed core dependencies include:

- `huggingface_hub`
- `lightrag-hku<1.5`
- `mineru[core]>=3.4.1`
- `tqdm`

## Not Yet Verified

- Installation
- Dependency compatibility with project/MinerU environments
- Real B01 `content_list` insertion
- Evidence round-trip
- Citation accuracy
- Image-only Equation behavior
- Operational storage/index lifecycle

## Intended Boundary

```text
PDF
→ MinerU
→ middle_json
→ MinerUAdapter v2
→ Unified Document + Evidence Store
→ RAGAnythingAdapter
→ content_list
→ RAG-Anything / LightRAG
```

RAG-Anything must not become the project's factual database. Schema simplification during indexing must never delete the authoritative Evidence chain.

## Adoption Gate

Do not mark `ADOPT` until an isolated environment demonstrates:

1. compatible installation without contaminating `.venv` or `.venv-mineru`;
2. direct B01 insertion from Unified Document-derived `content_list`;
3. stable Evidence/citation round-trip;
4. acceptable handling of text, images, Tables, and image-only Equations;
5. reproducible tests and documented rollback.
