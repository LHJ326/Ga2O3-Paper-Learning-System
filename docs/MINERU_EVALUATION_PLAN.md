# MinerU Evaluation Plan

## Purpose

MinerU is the first PDF parser candidate selected for testing. This is a test-order decision, not a final parser selection.

The evaluation objective is to verify whether MinerU satisfies the documented [B01 Parser Requirements](B01_PARSER_REQUIREMENTS.md). No capability is considered validated until the B01 benchmark has been run and its evidence reviewed.

## Test Input

Benchmark:

B01_standard_photodetector

Document:

Mg-doped α-Ga2O3 Nanorods for the Construction of Photoelectrochemical-Type Self-Powered Solar Blind UV Photodetectors and Underwater Imaging Application

DOI:

`10.1002/advs.202413074`

Input:

`data/benchmark/B01/B01.pdf`

The exact input file, checksum, page count, and source location must be recorded before execution so every result can be reproduced.

## Evaluation Items

### Document Structure

Check:

- title
- abstract
- sections
- references

### Reading Order

Check:

- two-column order

Paragraph sequence must be compared with B01 Ground Truth, including column transitions and page boundaries.

### Figure Extraction

Legacy / unverified historical expectation (not valid Ground Truth for the registered PDF):

- 4 figures
- 14 subfigures

Check:

- image
- caption
- page location

Figure ids and parent/subfigure relationships must remain traceable through adapter conversion.

### Equation Extraction

Legacy / unverified historical expectation (not valid Ground Truth for the registered PDF):

- 7 equations

Check:

- formula preservation
- location

Equation content must be compared in a normalized representation without discarding its source reference.

### Scientific Text Blocks

Check:

- background
- method
- result
- interpretation

Uncertain text-block classifications must remain explicit and linked to the original block.

### Schema Conversion

```text
MinerU output

↓

Adapter

↓

Unified Document Schema
```

Native output must be preserved separately from the adapter output. The adapter must not invent missing content or remove page-level evidence.

## Evaluation Result Template

Tool:

Version:

Environment:

Date:

Results:

Problems:

Decision:

The `Decision` field remains empty until benchmark evidence and problems have been reviewed against the evaluation matrix.
