# v0.1.0 Clean Installation Test

## Purpose

This record verifies the documented first-time installation workflow from an
isolated clone. The test does not reuse the project's existing virtual
environment, source PDFs, MinerU ZIP archives, `.env`, MinerU environment, or
FAISS index.

## Test Environment

- Date: 2026-09-29
- Operating system: Windows
- Shell: PowerShell
- Tested source commit: `5374c51` plus the Phase 6.1 portability fixes recorded
  by this document
- Python: 3.12.7
- pip after upgrade: 26.2.1
- Project: `ga2o3-paper-learning-system` 0.1.0, editable install
- FAISS: `faiss-cpu` 1.15.1

The clone initially contained no `.env`, source PDF, FAISS index, or prebuilt
virtual environment.

## Virtual Environment Creation

From the isolated clone root:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Observed Python version: `Python 3.12.7`. The new environment initially used
pip 24.2 and upgraded successfully to pip 26.2.1.

## Package Installation

The README command was executed unchanged:

```powershell
python -m pip install -e .
```

The editable wheel for version 0.1.0 built successfully. All declared runtime
dependencies installed, including PyYAML, PyMuPDF, bibtexparser,
python-dotenv, NumPy, pandas, and `faiss-cpu`. The following verification passed:

```powershell
python -m pip check
```

Result: `No broken requirements found.`

Imports were also verified for `src.ingestion`, `src.metadata`, `src.knowledge`,
`src.paper_object`, `src.registry`, `src.embedding`, `src.vectorstore`, and
`src.rag`.

## Test Run

Command:

```powershell
python -m pytest -q
```

Clean-clone result:

```text
205 passed, 3 skipped
```

The skipped checks require assets intentionally excluded from the public
repository:

1. The separately managed `.venv-mineru` environment.
2. The user-provided P001 source PDF.
3. The B02 source PDF used by one OCR cache-hit integration check.

In the fully provisioned development workspace, where those assets exist, the
same suite reports `208 passed`.

## Portability Findings and Fixes

The first Windows clone exposed automatic CRLF conversion in byte-frozen parser
fixtures. `.gitattributes` now defines explicit line endings for frozen MinerU
and OCR artifacts, making their SHA-256 checksums reproducible across Windows
and POSIX checkouts.

Environment-only tests now skip only when their external asset is absent. They
continue to run and pass in a fully provisioned workspace. Editable-install
metadata (`*.egg-info/`) and build output are ignored so installation does not
dirty the clone.

## Verified Functionality

- Editable package build and installation
- Dependency resolution and `pip check`
- Package imports across all public architecture layers
- Metadata and batch-ingestion unit behavior
- Unified Document and MinerU adapter fixture processing
- Knowledge schemas, extraction frameworks, validators, and writers
- Paper Object and Registry behavior
- Evidence-linked chunking
- Local FAISS add/search/save/load with mock vectors
- Evidence-aware retrieval without LLM generation

No real DeepSeek, Embedding, MinerU, or OCR API/runtime call was made during the
installation test.

## Remaining External Requirements

- Users must provide papers they are authorized to process.
- MinerU and ordinary PaddleOCR remain separately managed runtimes.
- Real DeepSeek extraction requires a local `DEEPSEEK_API_KEY`.
- v0.1.0 does not select a production embedding model or provide generated RAG
  answers.
