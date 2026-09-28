# Experiment Log

## Experiment — TABLE-LIGHT-2 Runtime Integration

Date: 2026-09-28

Objective: Remove manual crop/OCR steps while preserving the existing
TABLE-LIGHT-1 deterministic reconstruction and frozen benchmark layers.

Procedure: Detected structural table failures from DocVortex middle JSON,
localized two bounded PDF regions without GT, rendered at 288 DPI, invoked the
existing external ordinary PaddleOCR environment via subprocess, hashed and
cached raw results, applied measured crop-to-PDF transforms, reconstructed, and
evaluated a separate runtime Layer C. A second run verified cache reuse.

Results: two candidates, two localized regions, two initial OCR calls, then two
cache hits and zero repeat calls. Table I reconstructed as 10×3 and Table II as
14×7. Detection TP/FP/FN was 2/0/0. Runtime exact/semantic cells were 29/30 for
Table I and 85/98 exact, 86/98 semantic for Table II. Frozen fixture scores and
Layer A/B stayed unchanged.

Conclusion: the runtime architecture is complete and Evidence reaches original
PDF coordinates. Automatic crop/OCR text quality is the remaining known issue;
PaddleOCR-VL remains optional extreme fallback. `OCR-ENV-CLEANUP` was not run.

## Experiment — B02 Raw MinerU + Current Adapter v2 Baseline

Date: 2026-09-28

Objective: Freeze the B02 cross-domain parser/table stress baseline without
changing Ground Truth, Raw Output, or MinerUAdapter parsing logic.

Setup: B02 Ground Truth `ready_v1`; MinerU 4.0.7 `docvortex.middle` 2.0 Raw
Output; current MinerUAdapter v2; independently reviewed Raw block locators.

Procedure: Verified all three Raw SHA256 fingerprints, evaluated Layer A and
Layer B independently, preserved table and reading-order error cases, and ran
the complete test suite.

Results: Layer A detected 20 scientific Figures from 26 image blocks, 17 typed
Figure captions, 9 true-positive Equations plus one false positive, and zero of
two Tables. Layer B emitted 12 Pages, 27 heading records, 133 TextBlocks, 16
Figures, 10 Equations, and zero Tables. Table precision is N/A under the explicit
zero-prediction policy; recall is 0%.

Conclusion: B02 proves that a Table Vision Fallback is required before Parser
v1 freeze. MinerU 4.0.7 emitted no table entity for either real body Table.

Next Action: In a separately authorized phase, evaluate PaddleOCR-VL or an
equivalent table-capable vision parser without changing the frozen baseline.

## Experiment — Lightweight OCR Table Reconstruction

Date: 2026-09-28

Objective: Engineer the user-validated PyMuPDF crop + ordinary PP-OCR result
path from immutable OCR tokens/bboxes to Unified Tables with Evidence.

Setup: Two manually generated PaddleOCR 3.7.0 JSON artifacts; no OCR runtime
invocation; B02 Ground Truth and MinerU Raw frozen; Layer A/B historical result
read-only.

Procedure: Imported JSON only, registered crop-space metadata and checksums,
implemented conservative normalization, y/x clustering, multiline joining,
repeated-header multi-block unfolding, empty cells, confidence aggregation,
footnote separation, Unified Table Evidence, and independent Layer C scoring.

Results: Table detection improved from TP/FP/FN 0/0/2 in Layer A/B to 2/0/0 in
Layer C. Table I is 10×3 with 30/30 exact core cells. Table II is 14×7 with
98/98 occupied, 97/98 exact, and 98/98 semantic-normalized core cells; A-D
markers were recovered. No Ground Truth, MinerU Raw, Adapter logic, or baseline
result was modified.

Conclusion: Lightweight reconstruction is a viable primary Table fallback
architecture. Parser v1 freeze still requires runtime crop/OCR integration,
coordinate transforms, and failure thresholds. PaddleOCR-VL remains optional.

Next Action: Separately authorize Lightweight Table runtime integration; keep
`Phase OCR-ENV-CLEANUP` deferred.
