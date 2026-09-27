# B01 Parser Benchmark Report

## B01 Identity

- Benchmark ID: `B01`
- Title: Mg-doped α-Ga2O3 Nanorods for the Construction of Photoelectrochemical-Type Self-Powered Solar Blind UV Photodetectors and Underwater Imaging Application
- Journal: Advanced Science
- Year: 2025
- DOI: `10.1002/advs.202413074`
- Role: Primary Parser Benchmark Case
- PDF SHA256: `71D5B029EA9928A261DB783597B00F06A48B156122DB69AE3F83D1B8275E9E7E`

## Evaluation Scope

This v1 report completes Layer A only:

```text
Ground Truth
    vs
MinerU 4.0.7 middle_json raw output
```

Layer B (`Unified Document / Adapter Output`) remains explicitly `NOT_EVALUATED`. The current adapter is not refactored to consume `docvortex.middle` in this phase.

Reviewed raw-block classifications are stored separately in `data/benchmark/B01/B01_RAW_REVIEW.yaml`. They capture the user's manual TP/FP/FN decisions and prevent the evaluator from treating every image or Equation block as scientifically valid.

## Ground Truth Summary

| Category | Ground Truth |
|---|---:|
| Pages | 10 |
| Main sections | 4 |
| Experimental subsections | 4 |
| Scientific Figures | 5 |
| Equations | 7 |
| Main-text Tables | 0 |

The current YAML has detailed Figure entries for Figures 1–3 only, while the manually confirmed benchmark summary and reviewed Raw mapping identify Figures 1–5 on pages 3, 4, 5, 7, and 8. The evaluator records this annotation-detail gap as a known issue and does not alter the Ground Truth file.

## MinerU Raw Summary

- Parser: MinerU 4.0.7
- Schema: `docvortex.middle`
- Schema version: `2.0`
- Pages: 10
- Raw image blocks: 6
- Raw Equation blocks: 8
- Raw `image_caption` blocks: 5
- Raw Table blocks: 0
- Raw `paragraph_title` blocks: 9

## Metrics

| Category | GT | Predicted | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Pages | 10 | 10 | 10 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| Scientific Figures | 5 | 6 | 5 | 1 | 0 | 0.8333 | 1.0000 | 0.9091 |
| Equations | 7 | 8 | 6 | 2 | 1 | 0.7500 | 0.8571 | 0.8000 |
| Figure captions | 5 | 5 | 5 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| Main sections | 4 | 9 | 4 | 5 | 0 | 0.4444 | 1.0000 | 0.6154 |
| Main-text Tables | 0 | 0 | 0 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |

For sections, the five additional `paragraph_title` blocks are valid ancillary headings rather than missing main sections: Supporting Information, Acknowledgements, Conflict of Interest, Data Availability Statement, and Keywords. They remain reported as extra relative to the four-item main-section Ground Truth.

## Page Results

- Page count match: yes
- Ground Truth pages: 10
- MinerU pages: 10
- Page coverage: 100%
- Missing pages: none
- Extra pages: none

## Figure Results

Five Scientific Figures were correctly recovered on PDF pages 3, 4, 5, 7, and 8.

False positive:

- PDF page 1, Raw image block index 2: Advanced Science Open Access publisher logo

False negatives: none.

## Equation Results

Six of seven Ground Truth Equations were represented by Raw Equation blocks.

False negative:

- Equation (2), PDF page 2: `Ga(OH)3 → GaOOH + H2O`

False positives:

- PDF page 9, Raw Equation block index 9: Advanced Science Open Access publisher logo
- PDF page 10, Raw Equation block index 33: Advanced Science Open Access publisher logo

No OCR or inferred formula reconstruction was performed.

## Caption Results

- Ground Truth Figure caption count: 5
- Predicted `image_caption` count: 5
- Caption coverage: 100%
- Conservatively matched Figure numbers: 1, 2, 3, 4, 5
- Unnumbered caption blocks: 0

Matching uses only the explicit leading `Figure N` label. No semantic similarity score is used.

## Section Results

All four main sections were conservatively matched by normalized title:

1. Introduction
2. Results and Discussion
3. Conclusion
4. Experimental Section

Missing main sections: none.

All four Experimental Section subsections were also identified from their explicit leading labels in text blocks:

- Reagents and Substrate
- Preparation and Modulation of Materials
- Material Characterization and Performance Tests
- Device Preparation and Application Design

The subsection results are reported separately from main sections.

## Table Results

- Ground Truth main-text Tables: 0
- Raw Table blocks: 0
- Result: true negative / no false positive

References to Supplementary Tables S1 and S2 do not create main-text Table entities.

## Known Issues

- Ground Truth YAML contains three detailed Figure records, while the manually confirmed v1 summary contains five. The benchmark uses the separate reviewed Raw mapping for the confirmed five-Figure count and leaves Ground Truth unchanged.
- Raw Equation classification confuses the publisher logo with Equations on pages 9 and 10.
- Equation (2) is missing from Raw Equation blocks.
- Layer B is not evaluated because the current MinerUAdapter does not consume `docvortex.middle` schema 2.0.

## Architectural Finding

MinerU 4.0.7 `middle_json` using `docvortex.middle` schema 2.0 exposes structured types including:

- `header`
- `footer`
- `page_footnote`
- `paragraph_title`
- `equation`
- `image`
- `image_caption`
- `doc_title`

This structure preserves page/block typing and stable Raw locators more directly than Markdown. Therefore, `middle_json` should be the primary input candidate for MinerUAdapter v2. The existing Markdown route should remain as a fallback until a separate adapter phase designs, implements, and benchmarks the migration.
