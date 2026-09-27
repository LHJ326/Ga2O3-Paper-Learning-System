# B02 Parser Stress Benchmark Baseline

## Scope and frozen inputs

This report freezes the B02 baseline for MinerU 4.0.7 Raw Output (Layer A) and
the current MinerUAdapter v2 Unified Document output (Layer B). The B02 Ground
Truth was finalized as `ready_v1` before MinerU parsing and was not changed by
this benchmark. MinerU was not rerun, Raw Output was not modified, and Adapter
parsing logic was not changed.

| Input | SHA256 |
|---|---|
| `data/parsed/B02/mineru/raw/markdown/B02.md` | `BD29EE13FD294D8011F951AEB6FC4B7686ABF1030C396B49CB11FB56D3E2DF29` |
| `data/parsed/B02/mineru/raw/middle_json/B02.json` | `E1A2E3F8E2BD2D295FC95F536BAB69CBA196376D85FF0706212C5A59A78C9E1D` |
| `data/parsed/B02/mineru/raw/zip/B02.zip` | `A01FAAC480C30811D39B3468525DE6851422644A7EC40D046F3DA5420815B9E3` |

The evaluated machine-readable input is `docvortex.middle`, schema version
`2.0`, with 12 pages. Reviewed Raw classifications and locators are preserved
in `data/benchmark/B02/B02_RAW_REVIEW.yaml`; full metrics are preserved in
`data/benchmark/B02/B02_BENCHMARK_RESULT.json`.

## Layer A — Raw MinerU

| Category | GT | Predicted | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Pages | 12 | 12 | 12 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| Main Sections | 5 | 5 | 5 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| Subsections | 15 | 15 | 15 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| Scientific Figures | 20 | 26 image blocks | 20 | 6 | 0 | 76.92% | 100.00% | 86.96% |
| Figure captions | 20 | 17 typed captions | 17 | 0 | 3 | 100.00% | 85.00% | 91.89% |
| Equations | 9 | 10 | 9 | 1 | 0 | 90.00% | 100.00% | 94.74% |
| Tables | 2 | 0 | 0 | 0 | 2 | N/A | 0.00% | 0.00% |

Raw Figure scoring uses reviewed image-block locators rather than assuming that
all 26 image blocks are scientific Figures. The six false positives comprise
the Table II body on page 11 and five author portraits on page 12. The 17 typed
`image_caption` blocks omit correctly typed/attached captions for Figures 3, 8,
and 13. Figure 3 and Figure 13 captions were typed as `paragraph_title`; Figure
8 has no attached typed caption. Page 10 also attaches the Figure 18 and Figure
19 captions to a single image block.

The Raw Equation distribution is three blocks on page 2, five on page 3, one on
page 4, and one false-positive block on page 12. No automatic correction is
applied.

## Layer B — Current MinerUAdapter v2

The current Unified Document contains 12 Pages, 27 Section/heading records, 133
TextBlocks, 16 Figures, 10 Equations, and 0 Tables. Main Section and Subsection
metrics are evaluated independently from the total heading-record count.

| Category | GT | Predicted | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Pages | 12 | 12 | 12 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| Main Sections | 5 | 5 | 5 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| Subsections | 15 | 15 | 15 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| Scientific Figures | 20 | 16 | 16 | 0 | 4 | 100.00% | 80.00% | 88.89% |
| Figure captions | 20 | 16 | 16 | 0 | 4 | 100.00% | 80.00% | 88.89% |
| Equations | 9 | 10 | 9 | 1 | 0 | 90.00% | 100.00% | 94.74% |
| Tables | 2 | 0 | 0 | 0 | 2 | N/A | 0.00% | 0.00% |

Layer B is computed independently and does not overwrite Layer A. The Adapter's
caption-gated Figure rule removes the Table II image and all author portraits,
but it cannot emit Figures whose captions are absent, mistyped, or incorrectly
attached. The page-12 Equation false positive remains. Tables remain empty
because the Raw structural output contains no table entity; this benchmark does
not add recovery logic.

## Table failure cases

### Table I — `TABLE_BODY_MISSING`

On PDF page 8, `TABLE I` (Raw block 14) and `NIST 800-22 RANDOMNESS TEST`
(Raw block 15) were emitted as `paragraph_title`. The table body—ten test names,
ten P-values, and ten Pass values—was not emitted as a table entity or as
recoverable ordinary text rows.

### Table II — `TABLE_MISCLASSIFIED_AS_IMAGE`

On PDF page 11, `TABLE II` was emitted as `paragraph_title`, its title as text,
and its body as image block 4 with bbox `[0.14, 0.103, 0.856, 0.433]`. No cell
structure was produced.

The table zero-prediction policy reports precision as **N/A**, not zero, because
there is no positive prediction denominator. Recall and F1 are 0.00%.

## Reading-order known issue

Page 11 contains `READING_ORDER_ERROR_PAGE_11`. Raw block order places Table II,
Figure 20, right-column conclusion continuation, `REFERENCES`, left-column
Section IV.E continuation, and then `V. CONCLUSION`. This differs from the
manually confirmed logical reading order. The issue is reported without repair.

## Architectural finding

B02 proves that a Table Vision Fallback is required before Parser v1 freeze.
MinerU 4.0.7 produced no `table`, `table_caption`, or table-related structural
entity for either real body Table across the reviewed `middle_json`,
`model_output`, and `structured_content` layers. A future phase should evaluate
PaddleOCR-VL or an equivalent table-capable vision parser as an independent
fallback. No such dependency or fallback is installed or implemented here.
