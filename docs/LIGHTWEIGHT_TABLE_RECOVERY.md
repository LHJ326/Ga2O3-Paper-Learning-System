# Lightweight OCR Table Recovery

## Decision

The preferred Table fallback is:

```text
MinerU native Table
  ├─ success → use native structured Table
  └─ failure → locate probable Table region
               → PyMuPDF crop
               → ordinary PP-OCR
               → OCR tokens + crop-space bbox
               → deterministic spatial reconstruction
               → Unified Table + Evidence
               → optional extreme fallback only if unresolved
```

PaddleOCR-VL is an **optional extreme fallback**, not a default dependency and
not part of the current runtime path. On native Windows with an RTX 4060 Laptop
GPU (8 GB), the manually tested single-page cost was unacceptable.

## Manual Intervention Record

Before this phase, the user manually validated ordinary PaddleOCR in:

`<EXTERNAL_RESEARCH_ROOT>\PaddleOCR\.venv-paddleocr`

Recorded versions are PaddlePaddle GPU 3.2.1, PaddleOCR 3.7.0, and PaddleX
3.7.2. The user also manually created PyMuPDF crops and OCR results for B02
Table I and Table II. This phase did not rerun OCR, import the external runtime,
invoke it through subprocess, or copy any PNG artifact.

The two imported immutable JSON artifacts are registered in
`data/parsed/B02/light_ocr/B02_LIGHT_OCR_MANIFEST.yaml`. Their bbox values are
explicitly `crop_pixels`; no crop-to-PDF transform was available, so the
Evidence does not claim PDF-space coordinates.

## Reconstruction contract

`OCRToken` preserves `raw_text`, conservative `normalized_text`, confidence,
page, source artifact, coordinate space, and bbox geometry. The reconstructor:

1. selects token centers inside the configured crop-space Table region;
2. separates wide footnote candidates;
3. clusters y-centers into physical rows;
4. clusters x-centers into column anchors;
5. joins generic multiline continuations;
6. detects repeated header periods and unfolds side-by-side column groups;
7. materializes explicit empty cells and aggregated confidence;
8. emits a Unified `Table` with per-cell token indices and bboxes.

No reconstruction rule checks B02, a page number, an expected row count, or a
cell value. B02-specific page/region metadata lives only in the artifact
manifest. Ground Truth is used only by the independent evaluator after
reconstruction.

Normalization trims and collapses whitespace, unifies common Unicode variants,
normalizes micro signs and conservative tilde/hyphen variants, and preserves
scientific digits and footnote markers. It does not infer missing values or
replace OCR text using Ground Truth.

## B02 Layer C results

Layer A and Layer B remain byte-equivalent to the frozen B02 baseline. Layer C
is stored separately in
`data/benchmark/B02/B02_LIGHTWEIGHT_TABLE_RECOVERY_RESULT.json`.

| Metric | Before (Layer A/B) | Layer C |
|---|---:|---:|
| Table TP / FP / FN | 0 / 0 / 2 | 2 / 0 / 0 |
| Precision / Recall / F1 | N/A / 0% / 0% | 100% / 100% / 100% |

### Table I

- Structure: 10 logical rows × 3 columns
- Occupancy: 30/30 core cells
- Exact normalized core cells: 30/30
- Side-by-side physical blocks were unfolded from the repeated header pattern
- First row: `Frequency | 0.8343 | Yes`
- Last row: `AppEN | 0.1388 | Yes`

### Table II

- Structure: 14 logical rows × 7 columns
- Occupancy: 98/98 core cells
- Exact normalized core cells: 97/98
- Conservative semantic-normalized core cells: 98/98
- Footnote markers recovered: A, B, C, D
- Exact footnote bodies: B, C, D

The one exact core-cell mismatch is the OCR form `216μm2 B (1.54x)` versus the
source's superscript form `216μm² B (1.54x)`. Semantic comparison treats the
superscript glyph variant as equivalent while preserving the original OCR text.
Footnote A retains OCR punctuation (`"` where the source uses multiplication
dots); it is not silently repaired. Table II's blank upper-left header cell is
kept blank rather than inventing a value.

## Evidence chain

Each Unified Table records the OCR producer/version, source JSON, source page,
crop-space Table region, coordinate-space declaration, token indices/locators,
and confidence summary. Each cell records its own bbox and token indices:

```text
Unified Table Cell
→ rec_texts[index] / rec_boxes[index] / rec_scores[index]
→ immutable OCR JSON
→ registered PDF page and crop-space region
```

## Parser v1 assessment

The deterministic reconstruction layer is good enough as the lightweight Table
architecture baseline: it recovers both B02 structures with full occupancy and
100% semantic core-cell agreement. It is **not yet sufficient to freeze Parser
v1**, because runtime table-failure detection, region localization, PyMuPDF
crop generation, ordinary OCR invocation, coordinate transforms, and failure
thresholds remain outside this phase.

## Deferred environment cleanup

`Phase OCR-ENV-CLEANUP` remains a future, separately authorized task:

- establish an isolated minimal ordinary-OCR environment;
- freeze exact requirements;
- validate ordinary OCR on Table I and Table II;
- remove PaddleOCR-VL model caches;
- remove unneeded VL dependencies;
- decide whether the 1.87 GiB PaddleOCR source checkout is still required;
- retain every component required by ordinary OCR.

No cleanup is performed in this phase.

## TABLE-LIGHT-2 Runtime Integration

The default path is now implemented as MinerU structural output → generic
failure detection → PDF-space localization → PyMuPDF localized crop → external
ordinary PP-OCR → deterministic cache → existing spatial reconstruction →
Unified Table and Evidence. The main environment never imports PaddleOCR or
PaddlePaddle. `TABLE_OCR_EXECUTABLE` or explicit runtime configuration selects
the external interpreter; unavailable and failed runtimes return explicit
nonfatal states.

Detection supports common Roman and Arabic table designators, suppresses
fallback when a valid native table exists, and records `TABLE_BODY_MISSING` or
`TABLE_MISCLASSIFIED_AS_IMAGE`. Localization prefers nearby uncaptioned image
geometry and otherwise derives a conservative column crop and structural lower
boundary. No Ground Truth, paper ID, page number, or cell value participates.

Runtime manifests record PDF/crop/OCR hashes, 1-based page, PDF bboxes, DPI,
actual x/y render scales, backend settings, command metadata, source anchors,
and raw JSON. OCR tokens and Unified Table cells retain both crop-pixel and
PDF-space bboxes. Cache identity is deterministic and excludes absolute paths.
Large reproducible crop PNGs are ignored by Git.

The B02 smoke test found two candidates and called ordinary PP-OCR twice. The
second identical run yielded two cache hits and no OCR calls. Runtime structure
was Table I 10×3 and Table II 14×7, with table detection TP/FP/FN 2/0/0. Text
quality from automatic crops was Table I 29/30 exact and Table II 85/98 exact,
86/98 semantic. Frozen TABLE-LIGHT-1 fixtures remain unchanged at 30/30 and
97/98 exact, 98/98 semantic. The gap is a known runtime-tuning issue and is not
repaired using Ground Truth.

PaddleOCR-VL remains an optional extreme fallback only. `OCR-ENV-CLEANUP`
remains the next separately authorized environment phase and was not executed.
