# B01 Benchmark Readiness Report

## B01 Identity

- Benchmark ID: `B01`
- Title: Mg-doped α-Ga2O3 Nanorods for the Construction of Photoelectrochemical-Type Self-Powered Solar Blind UV Photodetectors and Underwater Imaging Application
- Journal: Advanced Science
- Year: 2025
- DOI: `10.1002/advs.202413074`
- Role: Primary Parser Benchmark Case
- PDF: `data/benchmark/B01/B01.pdf`
- File size: 3,417,943 bytes
- SHA256: `71D5B029EA9928A261DB783597B00F06A48B156122DB69AE3F83D1B8275E9E7E`
- Identity record: `data/benchmark/B01/B01_METADATA.yaml`

The PDF was placed in the project manually by the user. Its recorded size and SHA256 were verified against the local file during Phase 1.5D-2A.

## P001 / B01 Identity Boundary

`P001` is a Pilot / Integration Test Paper. It validates the MinerU raw-output workflow, adapter conversion, evidence links, and Document Schema 0.2.

`B01` is the Primary Parser Benchmark Case. It is evaluated only against independently authored B01 Ground Truth.

The identities remain separated by role and storage:

- P001 input: `data/papers/P001.pdf`
- P001 parser output: `data/parsed/P001/mineru/raw/`
- B01 input: `data/benchmark/B01/B01.pdf`
- B01 Ground Truth template: `data/benchmark/B01/B01_GROUND_TRUTH.yaml`
- B01 Ground Truth specification: `benchmark/B01_standard_photodetector/B01_GROUND_TRUTH_SPEC.md`

P001 statistics must not be used as B01 expected values. B01 Ground Truth must not be generated from MinerU output or changed to fit parser output.

## PDF Status

Status: **PRESENT_AND_IDENTIFIED**

The B01 PDF exists at the registered path. No copy, download, external-library search, or parser execution was performed during registration.

## Ground Truth Status

Status: **READY_V1_WITH_DETAIL_GAP**

`data/benchmark/B01/B01_GROUND_TRUTH.yaml` now contains manually authored Ground Truth v1 for pages, sections, Equations, Tables, supplementary references, boilerplate, and reading-order notes. The manually confirmed summary records five Scientific Figures, but the YAML currently has detailed entries for Figures 1–3 only. This detail gap is recorded without changing the user's Ground Truth.

The earlier expected counts of 4 Figures, 14 subfigures, and 7 Equations are retained only as historical design records. They are **LEGACY / UNVERIFIED** and are not valid B01 Ground Truth for the registered PDF.

## Legacy Expectations

| Historical item | Historical value | Status |
|---|---:|---|
| Figures | 4 | LEGACY / UNVERIFIED |
| Subfigures | 14 | LEGACY / UNVERIFIED |
| Equations | 7 | LEGACY / UNVERIFIED |

Actual counts must be established through independent Ground Truth annotation. MinerU output must not be used to derive them.

## Existing Benchmark Files

- `data/benchmark/B01/B01.pdf` — registered benchmark source PDF
- `data/benchmark/B01/B01_METADATA.yaml` — fixed identity and checksum
- `data/benchmark/B01/B01_GROUND_TRUTH.yaml` — canonical manually authored Ground Truth v1
- `data/benchmark/B01/B01_RAW_REVIEW.yaml` — reviewed Raw block TP/FP/FN annotations
- `data/benchmark/B01/B01_BENCHMARK_RESULT.json` — machine-readable Layer A result
- `data/parsed/B01/mineru/raw/middle_json/B01.json` — evaluated MinerU Raw input
- `docs/B01_BENCHMARK_REPORT.md` — Layer A benchmark report
- `benchmark/B01_standard_photodetector/B01_GROUND_TRUTH_SPEC.md` — annotation scope and canonical-file pointer
- `docs/B01_PARSER_REQUIREMENTS.md` — parser capability requirements; historical counts marked legacy/unverified
- `docs/B01_EVALUATION_MATRIX.md` — evaluation design; historical counts marked legacy/unverified
- `configs/evaluation.yaml` — legacy numeric configuration retained with explicit status
- `docs/MINERU_EVALUATION_PLAN.md` — planned evaluation procedure; historical counts marked legacy/unverified

## Separation Status

Status: **SEPARATED_BY_IDENTITY_ROLE_AND_PATH**

The B01 identity is now fixed independently of P001. No P001 statistics are part of the B01 metadata or Ground Truth scaffold.

## Readiness Result

**LAYER_A_EVALUATED**

B01 identity and Ground Truth v1 are registered, and the Layer A MinerU Raw benchmark is complete. Layer B remains explicitly not evaluated.

## Blocking Issues

1. Complete detailed Ground Truth records for Figures 4 and 5 independently of parser output.
2. Define the aggregate evaluation score and passing threshold.
3. Design MinerUAdapter v2 separately before Layer B evaluation.
