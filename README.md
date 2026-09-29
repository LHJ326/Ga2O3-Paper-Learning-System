# Ga2O3 Paper Learning System

Ga2O3 Paper Learning System is an evidence-first research-paper engineering
pipeline for Ga₂O₃ optoelectronic-device literature. It converts parsed papers
into traceable knowledge assets and exposes those assets through local,
structured retrieval interfaces.

The project is designed for research workflows where a result is useful only
when it can be traced back to the source paper, page, parser element, and raw
locator. It does not treat an LLM response as the source of truth.

## Goals

- Build a reproducible path from papers to structured research knowledge.
- Preserve Evidence IDs, 1-based pages, source element types, and locators.
- Separate parsing, knowledge extraction, validation, indexing, and retrieval.
- Support batch paper lifecycle management without automatic paid API calls.
- Keep uncertain or unsupported knowledge visible for human review.

## Architecture

```text
PDF / RIS / BibTeX
        |
        v
Ingestion + Metadata
        |
        v
MinerU Adapter / Table Recovery
        |
        v
Unified Document + Evidence
        |
        v
Knowledge Extraction + Validation
        |
        v
Paper Object + Registry
        |
        v
Evidence-linked Chunks
        |
        v
Embedding Adapter -> Local FAISS Vector Store
        |
        v
Evidence-aware Retrieval (no answer generation)
```

The Unified Document and Evidence layers remain authoritative. Paper Objects,
embeddings, vector indexes, and retrieval results are derived assets. See
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for module boundaries and data
contracts.

## Current Features

- PDF batch ingestion and stable P-series paper IDs.
- RIS and BibTeX metadata import and normalization.
- MinerU 4.0.7 `docvortex.middle` schema 2.0 adapter with legacy fallback.
- Unified Document Schema 0.2 with page- and element-level Evidence.
- Lightweight table-failure detection and ordinary OCR recovery boundary.
- Core knowledge schema plus a Ga₂O₃ semiconductor domain extension.
- Summary, material/device, performance, and mechanism extraction pipelines.
- Validation for structure, Evidence coverage, units, and review warnings.
- Standard Paper Object assembly with lossless Evidence references.
- Multi-paper Registry and dry-run-first batch orchestration.
- Model-neutral embedding interfaces and evidence-linked chunking.
- Local FAISS storage with save/load and cosine-similarity search.
- Structured Evidence-aware retrieval without LLM answer generation.

The checked-in P001 embedding, vector-store, and RAG reports use deterministic
mock vectors. They validate wiring and traceability, not semantic retrieval
quality.

## Installation

Requirements:

- Python 3.12 or newer
- Git
- Windows, Linux, or another platform supported by the declared dependencies

Create an isolated environment and install the project:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

Linux/macOS:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Run the test suite:

```bash
python -m pytest -q
```

Public clones do not contain source PDFs, MinerU ZIP archives, or the external
MinerU virtual environment. Three environment-specific checks are therefore
skipped automatically; the remaining suite runs without those private/local
assets. Frozen parser fixtures use repository line-ending rules so checksum
tests are consistent on Windows and POSIX checkouts.

MinerU and the optional ordinary PaddleOCR fallback use separately managed
runtimes and are not installed by this package. The repository can consume
existing parser outputs without rerunning MinerU.

### Optional DeepSeek configuration

Real knowledge extraction is opt-in. Put the key in a local `.env` file:

```text
DEEPSEEK_API_KEY=your-key
```

`.env` files are ignored by Git. Never commit a key. A minimal connection test
is available, but it performs a real API request:

```bash
python scripts/test_deepseek_connection.py
```

No API call is made by tests, batch dry-runs, embedding preparation, local
vector-store tests, or retrieval dry-runs.

## Usage

The public repository does not include source PDFs. Supply papers you are
authorized to process in a local input directory.

### 1. Import papers

```bash
python -m src.ingestion path/to/input-pdfs --recursive
```

This creates or updates paper directories and Registry records. If matching
RIS/BibTeX metadata is supplied, the metadata pipeline associates it during
ingestion.

### 2. Produce parsed and knowledge artifacts

Parsing runtimes are external to the main environment. Existing parsed output
is converted into the Unified Document, then task-specific knowledge pipelines
produce validated Summary, Parameters, Performance, and Mechanism artifacts.
Real LLM runs are always explicit; they are never triggered by the default batch
dry-run.

### 3. Build a Paper Object

For the current reference paper workflow:

```bash
python scripts/build_p001_object.py
```

The resulting `paper_object.yaml` preserves all available Evidence references
and validation warnings.

### 4. Inspect downstream dry-runs

```bash
python scripts/prepare_p001_embeddings.py
python scripts/prepare_p001_vectorstore.py
python scripts/query_p001_rag.py --top-k 5
```

These commands use local deterministic mock vectors. They make no Embedding or
LLM API calls and do not mark production Registry stages complete.

## Data and Security

- `.env`, PDFs, local vector indexes, caches, and generated runtime crops are
  ignored by Git.
- Do not commit copyrighted papers, API keys, model caches, or private research
  data.
- Missing values remain null; validators do not silently invent or correct
  scientific claims.
- Items marked `review_required` should be checked against their Evidence before
  downstream use.

## License

The original software and documentation in this repository are released under
the [MIT License](LICENSE).

This project is a scientific learning and research-engineering tool. Its source
distribution does not include research-paper PDFs, third-party datasets, or
model weights. Users must supply only resources they are authorized to use and
must comply with the licenses and terms of MinerU, PaddleOCR, DeepSeek, FAISS,
PyMuPDF, and any other external software, service, model, or research content.
The project license does not grant rights to third-party papers or derived
third-party content.

## Roadmap

- Select and version a real embedding backend.
- Evaluate semantic retrieval quality against evidence-linked questions.
- Persist and validate multi-paper FAISS indexes.
- Extend batch Paper Object generation beyond the reference paper.
- Add cross-paper comparison on top of validated retrieval.
- Consider an answer-generation layer only after citation and retrieval quality
  gates are defined.

Generated answers, autonomous agents, and unsupported knowledge completion are
not part of v0.1.0.
