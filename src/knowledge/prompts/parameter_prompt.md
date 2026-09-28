# Device Parameter Extraction Contract

Extract device and material parameters only from the supplied evidence. Map
values to fields defined by the loaded Domain Extension.

Rules:

- Preserve the reported value, unit, measurement conditions, and comparison basis.
- Do not convert, estimate, or normalize a value unless the transformation is explicit.
- Attach valid `evidence_id` values to each populated parameter.
- Leave unsupported fields null or absent.
- Do not introduce fields outside the loaded Domain Extension.
