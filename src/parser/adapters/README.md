# Parser Adapters

## Adapter layer purpose

The adapter layer isolates external parser-specific formats and converts them into the project's unified `Document` schema.

```text
External parser output

↓

Adapter conversion

↓

Unified Document Schema
```

Each future adapter must preserve page locations and source references, report unsupported or uncertain fields explicitly, and avoid leaking tool-specific data structures into downstream components.

No external parser adapter is implemented or registered in Phase 1.5A.
