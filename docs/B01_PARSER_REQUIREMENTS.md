# B01 Parser Requirements

This document defines the minimum parser capabilities to evaluate against the B01 Ground Truth. It specifies expected output, not the behavior of any particular parser.

> **Ground Truth status:** The historical numeric expectations in this document predate registration of the current B01 PDF. Values of 4 Figures, 14 subfigures, and 7 Equations are retained as **LEGACY / UNVERIFIED** only. Actual B01 counts must come from independent annotation in `data/benchmark/B01/B01_GROUND_TRUTH.yaml`, never from parser output.

## Document Level

The parser output must preserve:

- title
- authors
- abstract
- sections
- references

Document-level fields must be mapped into the unified `Document` schema with stable identifiers and source references. Missing fields must be reported explicitly rather than inferred without evidence.

## Reading Order

B01 contains:

- two-column layout
- paragraph sequences that must remain correct across columns and pages

The parser must reconstruct the intended reading order without interleaving unrelated columns, captions, headers, footers, or references. Paragraph boundaries and page locations must remain traceable.

## Figure Requirements

Legacy / unverified historical expectation:

- 4 figures
- 14 subfigures

The parser output must preserve:

- figure image
- caption
- figure id
- page location

Subfigures must remain associated with their parent figure. Caption-to-figure linkage must be explicit and must not depend only on output order.

## Equation Requirements

Legacy / unverified historical expectation:

- 7 equations

The parser output must preserve:

- equation content
- location
- variable meaning

Variable meaning must be linked to supporting nearby scientific text when present. A parser must not invent a variable definition when the source does not provide one.

## Evidence Chain Requirements

The parser and adapter must maintain the following traceable relationship:

```text
paragraph

↓

figure/equation

↓

source reference
```

Each extracted object must retain an identifier, page number, content, and source reference. Relationships between paragraphs, figures, captions, equations, and explanatory text must survive conversion into the unified `Document` schema.

## Scientific Text Block Requirements

Scientific text blocks must distinguish:

- background
- method
- result
- interpretation

Classification must remain connected to the original text block and source location. Uncertain classifications must be represented as uncertain rather than silently forced into a category.

## Priority Levels

| Priority | Level | Meaning |
|---|---:|---|
| Critical | ★★★★★ | Required for a parser candidate to pass the core B01 evaluation. |
| Important | ★★★★ | Strongly affects integration quality and downstream usability. |
| Optional | ★★★ | Useful capability that does not replace critical evidence requirements. |

Capability requirements in this document remain evaluation targets. The legacy numeric counts are not acceptance targets for the registered B01 PDF until replaced by reviewed Ground Truth, and they do not indicate that any candidate parser has passed.
