# Project State

Project:

Ga2O3-Paper-Learning-System

Current Phase:

Phase 1.5D-2C — B01 Benchmark Evaluator v1 completed

Completed:

- Project initialization
- Python development environment initialized
- MinerU isolated environment created
- MinerU 4.0.7 manually installed and verified
- Parser interface and Document Schema initialized
- Paper library structure created
- MinerU raw-output contract defined
- P001 PDF imported and registered
- P001 MinerU raw output generated
- P001 MinerU raw output analyzed
- MinerUAdapter first conversion implemented
- Project session handover created
- AI session memory created
- P001 Figure-caption mapping implemented
- Scientific figure asset filtering implemented
- Figure-to-text evidence chain implemented
- Supplementary Figure references classified
- MinerU formula assets mapped to Document.equations
- P001 Table detection completed
- P001 Document integrity validation completed
- Repeated publisher/header/footer boilerplate filtering implemented
- Document Schema 0.2 stabilized
- Typed Evidence object added
- Typed Figure/TextBlock relations added
- Typed Equation metadata added
- P001 Adapter / Schema 0.2 reached the current Pilot stable node
- B01 benchmark readiness and P001/B01 identity separation assessed
- B01 PDF manually placed by the user
- B01 identity and SHA256 registered
- B01 Ground Truth scaffold initialized
- Legacy B01 expected counts marked LEGACY / UNVERIFIED
- B01 Ground Truth v1 manually established
- B01 MinerU 4.0.7 Raw Output manually generated
- B01 Layer A parser benchmark evaluator implemented
- B01 machine-readable benchmark result generated
- B01 parser benchmark report generated

Current Data:

P001:

Role:

Pilot / Integration Test Paper

PDF:

`data/papers/P001.pdf`

Raw Output:

`data/parsed/P001/mineru/raw/`

Document:

Generated through `MinerUAdapter.convert()`

Current Document Statistics:

- Pages: 12
- Sections: 10
- TextBlocks: 156
- Figures: 6
- Tables: 0
- Equations: 6
- FigureTextRelations: 40

B01:

Role:

Primary Parser Benchmark Case

Title:

Mg-doped α-Ga2O3 Nanorods for the Construction of Photoelectrochemical-Type Self-Powered Solar Blind UV Photodetectors and Underwater Imaging Application

Journal / Year / DOI:

Advanced Science / 2025 / `10.1002/advs.202413074`

PDF:

`data/benchmark/B01/B01.pdf`

SHA256:

`71D5B029EA9928A261DB783597B00F06A48B156122DB69AE3F83D1B8275E9E7E`

Metadata:

`data/benchmark/B01/B01_METADATA.yaml`

Ground Truth:

`data/benchmark/B01/B01_GROUND_TRUTH.yaml`

Benchmark readiness:

`LAYER_A_EVALUATED`

Ground Truth v1 confirms 10 pages, 4 main sections, 5 Scientific Figures, 7 Equations, and 0 main-text Tables. Layer A evaluates MinerU Raw Output against the manually reviewed evidence. Layer B remains a placeholder.

Current:

- B01 PDF manually available and identity fixed
- B01 Ground Truth v1 available
- Layer A Raw benchmark completed
- Figure Raw metrics: TP 5 / FP 1 / FN 0
- Equation Raw metrics: TP 6 / FP 2 / FN 1
- Layer B Unified Document benchmark not evaluated
- P001 and B01 separated by identity, role, and path

Current Recovery Files:

- `docs/PROJECT_STATE.md`
- `docs/SESSION_HANDOVER.md`
- `docs/AI_SESSION_MEMORY.md`
- `docs/MINERU_P001_OUTPUT_ANALYSIS.md`
- `docs/MINERU_ADAPTER_DESIGN.md`
- `docs/B01_BENCHMARK_READINESS_REPORT.md`
- `data/benchmark/B01/B01_METADATA.yaml`
- `data/benchmark/B01/B01_GROUND_TRUTH.yaml`
- `data/benchmark/B01/B01_RAW_REVIEW.yaml`
- `data/benchmark/B01/B01_BENCHMARK_RESULT.json`
- `docs/B01_BENCHMARK_REPORT.md`

Current Limitations:

- Scientific Figures require an `Image block` and a conservative same-page adjacent numbered caption
- 11 non-Figure assets remain only in Raw Output
- Supplementary Figure references remain unlinked because supplementary Figures are not part of the current Document
- Equation text remains unavailable because P001 Formula blocks are image-only
- One page-11 Formula block appears to be a MinerU reference-fragment misclassification
- Table extraction incomplete
- `parse()` / `validate()` remain interface placeholders
- B01 Ground Truth YAML has detailed Figure records for Figures 1–3 only, while the manually confirmed v1 summary records five Scientific Figures
- Layer B cannot yet evaluate `docvortex.middle` without a future MinerUAdapter v2 design
- B01 evaluation has no aggregate passing threshold

Known Issues:

- MinerU classified one page-11 reference fragment as a Formula block; Equation false-positive filtering is deferred to a later phase
- B01 Raw Equation blocks contain publisher-logo false positives on pages 9 and 10
- B01 Equation (2) is a Raw false negative on page 2

Next:

- Complete detailed Ground Truth records for B01 Figures 4 and 5 without using parser output
- Define the benchmark aggregate score / passing threshold
- Design MinerUAdapter v2 with `middle_json` as the primary input candidate and Markdown as fallback
- Implement Layer B evaluation only in a later adapter phase
