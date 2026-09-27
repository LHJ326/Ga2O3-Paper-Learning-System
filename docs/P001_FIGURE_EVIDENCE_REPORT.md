# P001 Figure Evidence Report

## Summary

- Total scientific Figures: 6
- Figures with explicit body references: 6
- Figures without explicit body references: 0
- Explicit body Figure reference occurrences: 63
- Resolved primary-Figure reference occurrences: 40
- Unresolved Figure reference occurrences: 23
- Unresolved-reference class: supplementary Figures not present in the current Document

Caption TextBlocks are excluded from body-reference counts. Repeated explicit references remain separate occurrences, while related TextBlock IDs are unique per Figure.

## Figure 1

- Caption: Figure 1. Biological synapse in the human visual system and FG memory device. a) Schematic illustration of the human visual system, including information reception and information processing. b) Schematic diagram of the working process of the biological synapse and the proposed FG memory device based on MoS2/Ga2O3/MLG van der Waals heterojunction.
- Figure page: 2
- Related TextBlock count: 1
- Related TextBlocks: `P001-text-0022`
- Detected textual references: `Figure 1a`, `Figure 1b`

## Figure 2

- Caption: Figure 2. The schematic and basic characterization of the MoS2/Ga2O3/MLG FG memory, including energy-band, structure, Raman, optical, SEM/EDS, and AFM characterization panels.
- Figure page: 3
- Related TextBlock count: 2
- Related TextBlocks: `P001-text-0024`, `P001-text-0032`
- Detected textual references: `Figure 2a`, `Figure 2b`, `Figure 2c`, `Figure 2d`, `Figure 2e,f`, `Figure 2g`

## Figure 3

- Caption: Figure 3. The schematic and basic electrical storage performance of the MoS2/Ga2O3/MLG FG memory device, including transfer, retention, endurance, charge-density, switching-ratio, and energy-band panels.
- Figure page: 4
- Related TextBlock count: 7
- Related TextBlocks: `P001-text-0035`, `P001-text-0044`, `P001-text-0058`, `P001-text-0059`, `P001-text-0062`, `P001-text-0063`, `P001-text-0064`
- Detected textual references: `Figure 3a`, `Figure 3b`, `Figure 3c`, `Figure 3d`, `Figure 3e`, `Figure 3f`, `Figure 3g`, `Figure 3h`, `Figure 3i`, `Figure 3j`

## Figure 4

- Caption: Figure 4. The physical mechanism of the optical FG memory and comparison of nonvolatile electrical/optoelectrical 2D FG memory devices.
- Figure page: 5
- Related TextBlock count: 5
- Related TextBlocks: `P001-text-0043`, `P001-text-0067`, `P001-text-0074`, `P001-text-0075`, `P001-text-0076`
- Detected textual references: `Figure 4g,h` (2 occurrences), `Figure 4a`, `Figure 4b`, `Figure 4e`, `Figure 4c`, `Figure 4f`, `Figure 4d`

## Figure 5

- Caption: Figure 5. Synapse simulation, including pulse response, potentiation, PPF, depression, and LTP/LTD characteristics.
- Figure page: 8
- Related TextBlock count: 4
- Related TextBlocks: `P001-text-0077`, `P001-text-0078`, `P001-text-0088`, `P001-text-0091`
- Detected textual references: `Figure 5a`, `Figure 5b`, `Figure 5c` (2 occurrences), `Figure 5d`, `Figure 5e`, `Figure 5f` (2 occurrences)

## Figure 6

- Caption: Figure 6. Neuromorphic computing application, including the VGG-8 model, neuron model, hardware implementation, classification accuracy, and confusion matrices.
- Figure page: 9
- Related TextBlock count: 4
- Related TextBlocks: `P001-text-0100`, `P001-text-0102`, `P001-text-0103`, `P001-text-0111`
- Detected textual references: `Figure 6a` (2 occurrences), `Figure 6b`, `Figure 6c`, `Figure 6d`, `Figure 6e`

## Unresolved References

The 23 unresolved occurrences are explicit supplementary-Figure references (`Figure S1` through `Figure S15`, including subfigure forms). They are preserved with normalized numbers and subfigure hints but are not linked because no corresponding supplementary Figure objects exist in the current Document. No missing primary Figure number and no ambiguous primary-Figure reference were detected.

## Evidence Rules

- Only explicit `Figure`, `Figures`, `Fig.`, or `Figs.` references are considered.
- Markdown emphasis markers are removed before pattern matching so forms such as `**Figure 1**a` remain detectable.
- Primary Figure numbers are normalized before lookup.
- Subfigure notation is retained as a hint and never creates an independent Figure.
- Captions are not counted as body citations.
- Missing and supplementary targets remain unresolved; no Figure is fabricated.
- Every linked Figure and TextBlock retains parser, source file, page, and MinerU locator fields where available.
