# Experiment Log

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
