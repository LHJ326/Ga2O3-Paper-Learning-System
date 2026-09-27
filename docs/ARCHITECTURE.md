# Architecture

Zotero/PDF/RIS

↓

Parser Layer

├── MinerU 4.0.7 `docvortex.middle` 2.0

└── Table fallback boundary
    ├── native structured Table when available
    └── PyMuPDF crop + ordinary PP-OCR result
        → deterministic spatial reconstruction
        → Unified Table + Evidence
        → optional PaddleOCR-VL extreme fallback only if unresolved

↓

Structured Document Layer

Unified Document Schema 0.2

Every recovered Table and cell retains source artifact, page, coordinate-space,
bbox, token locators, producer/version, and confidence evidence. Crop-space bbox
must never be represented as PDF-space without an explicit transform.

↓

Knowledge Layer

↓

RAG

↓

AI Tutor

PaddleOCR-VL is not a default dependency or current runtime path. Runtime OCR
invocation and `Phase OCR-ENV-CLEANUP` remain separately authorized future work.
