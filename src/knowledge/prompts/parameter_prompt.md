# Device Parameter Extraction Contract

Extract device and material parameters only from the supplied evidence. Map
values to fields defined by the loaded Domain Extension.

Rules:

- Extract only parameters explicitly stated in the supplied paper Evidence.
- Never infer, estimate, calculate, or fill a value from general knowledge.
- Preserve the reported value, unit, measurement conditions, and comparison basis.
- Do not convert, estimate, or normalize a value unless the transformation is explicit.
- Attach valid `evidence_refs` to every populated structured object or list item.
- Preserve the Evidence page and source reference in the returned Evidence index.
- Preserve reported units exactly; do not silently convert units.
- Set uncertain, ambiguous, or unsupported fields to `null`.
- Do not introduce fields outside the loaded Domain Extension.
