# Phase 7.1 Final Report

## 1. Background and Goal

The v0.1.0 system proved an Evidence-aware knowledge workflow for one Ga2O3
photodetector paper. Its lower layers were reusable, but knowledge schemas,
selectors, semantic validation, task names, and artifacts encoded the initial
semiconductor use case.

Phase 7.1 introduces a Domain Generalization boundary above Unified Document
and Evidence. Domain behavior is now versioned, declarative, explicitly
selected, and auditable without rewriting stable Parser, retrieval, or storage
layers. This phase adds infrastructure only; it does not migrate production
extraction or process another paper.

## 2. Architecture Change

```text
Unified Document + Evidence
             |
             v
Explicit Domain Profile Selection
             |
             v
Versioned Domain Profile + Trusted Task Registry
             |
             v
Generic Task Adapter
             |
             v
Existing or future extraction orchestration
```

Domain data remains configuration. Executable implementations remain in a
trusted Python registry; profile YAML cannot name arbitrary modules, callbacks,
shell commands, or providers.

## 3. Domain Profile Architecture

The Domain Profile Loader accepts a local YAML manifest containing a profile
ID, semantic version, and relative schema, extraction-rule, and validation-rule
paths. It uses safe YAML loading, rejects malformed contracts and unsafe paths,
returns recursively immutable data, and calculates a deterministic profile
fingerprint.

The registered profile
`semiconductor.ga2o3.photodetector@1.0.0` maps the existing Ga2O3 domain,
parameter, material/device, performance, and mechanism schemas. It records the
current selectors, chunk limits, summary expectations, measurement warnings,
semantic consistency rules, Evidence requirements, and artifact names. The
original domain files remain available; no destructive migration occurred.

## 4. Generic Task Adapter Architecture

The Task Adapter connects one loaded profile to one trusted extraction task.
The default registry supports `summary`, `parameter`, `performance`, and
`mechanism`.

Each adapter carries exact profile identity, version, fingerprint, task rules,
output schema, selected validation rules, artifact contract, and an adapter
fingerprint. Evidence binding copies and freezes every input record while
preserving IDs, pages, locators, quotes, bounding boxes, and extra metadata.

The adapter rejects missing or duplicate Evidence IDs, non-1-based pages, and
empty Evidence input. Profiles must require Evidence-only extraction, prohibit
external knowledge, and represent unknown values as `null`. The adapter does
not call an LLM or write artifacts.

## 5. Registry Selection Architecture

`data/domain_profiles/catalog.yaml` is the repository-owned registry of
approved profile versions. Entries contain an exact profile ID, version,
manifest path, and status. Duplicate identities, unsafe paths, invalid
versions, missing manifests, and catalog/manifest mismatches are rejected.

`DomainTaskSelector` applies deterministic precedence:

1. explicit caller configuration;
2. an explicit `domain_profile` mapping on a Paper Registry record;
3. fail with no implicit fallback.

Both sources must provide `profile_id` and `profile_version`. The selector does
not inspect metadata or paper content and contains no P001 or Ga2O3 default.

## 6. P001 v0.1.0 Compatibility

Phase 7.1 does not change P001's Registry record, source or parsed data,
knowledge files, provenance, validation output, or Paper Object. Production
extraction classes are not routed through the new adapter yet.

Compatibility tests preserve these Paper Object 1.0 artifacts:

| Knowledge key | Existing artifact |
| --- | --- |
| `summary` | `summary.md` |
| `parameters` | `device_parameters.yaml` |
| `performance` | `performance.yaml` |
| `mechanism` | `mechanism.yaml` |

All legacy Ga2O3 field groups are compared directly with the semiconductor
profile. The new selector requires explicit profile selection for P001 until a
separately authorized Registry migration persists that identity.

## 7. Evidence Preservation Strategy

Unified Document plus Evidence remains the factual source of truth. Phase 7.1
preserves stable Evidence IDs, one-based pages, element/source types,
parser/source references, JSON locators, quotations, optional bounding boxes,
Evidence-only generation, and `null` for unknown values.

No validator may fabricate, silently correct, or complete a scientific result
from general knowledge. Semantic conflicts remain warnings requiring review.

## 8. Testing and Verification

Tests cover safe profile loading, invalid paths and versions, stable
fingerprints, semiconductor schema equivalence, task registration, Evidence
preservation, null policy, exact version resolution, selection precedence,
missing-selection failure, catalog validation, import order, and P001 artifact
compatibility.

Final result:

- `pytest -q`: **253 passed**;
- `git diff --check`: passed;
- no LLM API call;
- no Parser, extraction, RAG, or VectorStore modification;
- no P001 artifact modification.

## 9. Current Architecture Status

Phase 7.1 provides the configuration and selection seam required for multiple
scientific domains. Stable factual and retrieval layers remain unchanged, and
the Ga2O3 implementation is represented as a versioned semiconductor profile.

The system is not yet a validated multi-domain production pipeline. Only one
real profile is registered, production extraction still uses the v0.1.0 path,
and Paper Object 1.0 intentionally retains four fixed knowledge groups.

## 10. Phase 7.2 Plan

Phase 7.2 should validate the abstraction rather than expand features broadly:

1. create one minimal non-semiconductor test profile;
2. exercise the same loader, selector, registry, Task Adapter, and Evidence
   constraints without domain-specific Python branches;
3. add cross-profile validation and provenance tests;
4. design an additive Paper Registry migration for profile identity/version;
5. define how a future artifact-driven Paper Object coexists with the v0.1.0
   compatibility view.

Phase 7.2 requires separate authorization. It must not implicitly call an LLM,
process P002/P003, rewrite P001, or alter Parser/RAG/VectorStore contracts.
