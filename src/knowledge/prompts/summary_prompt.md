# Summary Extraction Contract

Using only the supplied Unified Document elements and Evidence records, produce
a concise scientific summary covering the research problem, methodology, main
results, innovations, and stated limitations.

Rules:

- Do not add facts that are absent from the supplied evidence.
- Preserve units, conditions, and uncertainty.
- Attach valid `evidence_id` values to every factual claim in structured output.
- Report missing or ambiguous information as unknown.
- Return data that conforms to the loaded Core Knowledge Schema.
