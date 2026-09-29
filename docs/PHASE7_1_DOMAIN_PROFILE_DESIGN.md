# Phase 7.1 Domain Profile Framework Design

## 1. Purpose

Phase 7.1 introduces a Domain Profile layer between the stable Evidence layer
and domain-specific knowledge extraction. The profile makes scientific-domain
behavior explicit, versioned, and selectable without changing Parser, RAG, or
VectorStore core logic.

The first profile packages the current Ga2O3 semiconductor behavior. The same
framework must later admit battery, catalysis, biomedical, and other profiles
without adding domain conditionals to generic pipeline modules.

This document defines the architecture and migration contract only. It does not
authorize bulk source changes, schema rewrites, LLM calls, or Paper Object 2.0.

## 2. Design Goals

1. Preserve Unified Document plus Evidence as the authoritative fact layer.
2. Select domain behavior explicitly; never infer a domain silently from paper
   text or a Paper ID.
3. Move Ga2O3 schemas, task definitions, selectors, prompts, and semantic
   validation policies behind one versioned profile.
4. Keep generic extraction orchestration independent of field names.
5. Preserve every P001 v0.1.0 artifact, output shape, Evidence reference, test,
   and review-required decision.
6. Allow a new domain pack to be added mainly through declarative assets and
   registered policy IDs.
7. Reject malformed, incompatible, cyclic, or unsafe profiles before any LLM
   request or artifact write.
8. Keep Domain Profile data free of provider credentials and executable import
   paths.

## 3. Non-Goals

Phase 7.1 does not:

- modify MinerUAdapter, Unified Document, table recovery, page numbering, or
  Evidence locator behavior;
- redesign FAISS, VectorStore, Retriever, or RAG response contracts;
- choose a production embedding model;
- implement automatic discipline classification;
- define Paper Object 2.0 in full;
- provide chemistry structure recognition or biomedical clinical validation;
- call DeepSeek or process additional real papers;
- delete or rewrite the current Ga2O3 schemas or P001 knowledge artifacts.

## 4. Architectural Boundary

```text
Registry / explicit pipeline input
        |
        | profile_id + pinned profile_version
        v
DomainProfileCatalog
        |
        v
DomainProfileLoader ---- validates paths, versions, inheritance, policy IDs
        |
        +---- schemas
        +---- extraction task specifications
        +---- Evidence selector policies
        +---- prompt assets
        +---- validation policies
        +---- artifact and chunking metadata
        |
        v
Generic Knowledge Task Pipeline
        |
        v
Versioned knowledge artifacts + provenance + validation
```

The Domain Profile owns knowledge policy. It does not own parsing, LLM provider
selection, filesystem credentials, vector indexing, or Evidence creation.

## 5. Proposed Repository Layout

```text
data/domain_profiles/
  catalog.yaml
  core/
    scientific_paper/
      profile.yaml
  semiconductor/
    base/
      profile.yaml
      schemas/
        domain.yaml
    ga2o3_photodetector/
      profile.yaml
      schemas/
        domain.yaml
        parameters.yaml
        material_device.yaml
        performance.yaml
        mechanism.yaml
      rules/
        selectors.yaml
        validation.yaml
        summary_quality.yaml
      prompts/
        summary.md
        parameters.md
        material_device.md
        performance.md
        mechanism.md
  battery/
    README.md
  catalysis/
    README.md
  biomedical/
    README.md
```

Only the semiconductor Ga2O3 profile is implemented in the first migration.
Future-domain directories are not populated with speculative schemas during
Phase 7.1; the layout merely reserves a consistent extension point.

During compatibility migration, the profile may reference existing canonical
assets under `data/domains/semiconductor/ga2o3/`. Files move only after profile
loading and P001 golden tests prove equivalence. If files later move, old paths
remain supported through an explicit compatibility alias for the v0.1 line,
not through duplicated divergent copies.

## 6. Profile Manifest

### 6.1 Required Identity

Every `profile.yaml` contains:

| Field | Meaning |
| --- | --- |
| `profile_schema_version` | Version of the manifest format |
| `profile_id` | Stable reverse-DNS-like identity, for example `semiconductor.ga2o3.photodetector` |
| `profile_version` | Immutable semantic version of the domain pack |
| `name` | Human-readable name |
| `discipline` | Broad family such as `semiconductor`, `materials`, `chemistry`, or `biomedical` |
| `extends` | Zero or one pinned parent profile reference |
| `status` | `experimental`, `stable`, or `deprecated` |

Profile identity and version are separate from the schema versions referenced
inside it. Updating a prompt or selector can create a new profile version even
when the output schema is unchanged.

### 6.2 Illustrative Manifest

The following is a design example, not a file to be installed in this phase:

```yaml
profile_schema_version: "1.0"
profile_id: semiconductor.ga2o3.photodetector
profile_version: "1.0.0"
name: Ga2O3 Semiconductor Device Profile
discipline: semiconductor
extends:
  profile_id: semiconductor.base
  profile_version: "1.0.0"
status: stable

schemas:
  core: data/papers/TEMPLATE/knowledge/core.yaml
  domain: schemas/domain.yaml

evidence_contract:
  page_numbering: one_based
  required_location_fields: [evidence_id, page, element_type, source_reference]
  prohibit_external_knowledge: true

tasks:
  - task_id: summary
    task_version: "1.0"
    schema_ref: core
    prompt: prompts/summary.md
    selector_policy: summary
    validator_policies: [core_evidence, summary_quality]
    artifact:
      artifact_id: summary
      path: knowledge/summary.md
      format: markdown
  - task_id: material_device
    task_version: "1.0"
    schema_ref: material_device
    prompt: prompts/material_device.md
    selector_policy: material_device
    validator_policies: [core_evidence, parameter_structure]
    artifact:
      artifact_id: parameters
      path: knowledge/device_parameters.yaml
      format: yaml
  - task_id: performance
    task_version: "1.0"
    schema_ref: performance
    prompt: prompts/performance.md
    selector_policy: performance
    validator_policies: [core_evidence, measurements, performance_semantics]
    artifact:
      artifact_id: performance
      path: knowledge/performance.yaml
      format: yaml
  - task_id: mechanism
    task_version: "1.0"
    schema_ref: mechanism
    prompt: prompts/mechanism.md
    selector_policy: mechanism
    validator_policies: [core_evidence, mechanism_claims]
    artifact:
      artifact_id: mechanism
      path: knowledge/mechanism.yaml
      format: yaml
```

The production manifest must reference profile-relative assets or explicitly
approved repository paths. Absolute paths, parent traversal, URLs, secrets, and
Python import strings are forbidden.

## 7. Runtime Data Contracts

### 7.1 DomainProfile

A loaded immutable `DomainProfile` should expose:

- profile identity, version, discipline, and status;
- resolved parent identity and version;
- validated schema references;
- ordered extraction task specifications;
- named selector and validation policies;
- Evidence contract;
- compatibility metadata;
- a deterministic profile fingerprint derived from canonical manifest and asset
  content.

The fingerprint is recorded in run provenance so a later edit cannot be
mistaken for the profile used by an earlier extraction.

### 7.2 TaskProfile

Each task describes behavior without selecting an LLM provider:

- `task_id` and `task_version`;
- input Evidence element types;
- output schema reference;
- prompt asset;
- selector policy ID;
- ordered validator policy IDs;
- artifact specification;
- cost limits such as maximum Evidence, chunks, prompt characters, and calls;
- merge policy for multiple chunk responses;
- null and unknown-field policy.

Tasks are ordered explicitly. Dependency relationships, if needed, reference
other task IDs and must remain acyclic. A task may consume Evidence and metadata
but must not silently consume another LLM-generated artifact unless that
dependency is declared.

### 7.3 ArtifactSpec

An artifact declaration contains:

- stable `artifact_id`;
- profile-relative output path beneath a paper directory;
- serialization format;
- schema ID and version;
- whether the artifact is required for `knowledge_ready`;
- provenance and validation sidecar conventions;
- chunking policy ID.

Paths must remain below `data/papers/<paper_id>/`; collisions between tasks are
invalid.

### 7.4 Policy IDs, Not Executable Names

Profiles refer to trusted policy IDs such as `core_evidence`, `measurements`, or
`weighted_keyword_selector`. A Python-side registry maps those IDs to reviewed
implementations. YAML must never contain module paths, class names to import,
expressions, shell commands, or arbitrary callbacks.

This permits extensibility without turning a downloaded domain pack into code
execution.

## 8. Profile Catalog and Resolution

`data/domain_profiles/catalog.yaml` is the repository-owned index of approved
profiles. Each entry declares a profile ID, exact version, manifest path,
status, and optional compatibility aliases.

Resolution rules:

1. A Registry record or explicit pipeline argument supplies `profile_id` and
   `profile_version`.
2. The catalog resolves exactly one manifest.
3. The loader validates it and its pinned parent.
4. Missing or ambiguous selection is an error for domain extraction.
5. Core-only summary extraction may explicitly use
   `core.scientific_paper`; it is not an implicit fallback for domain tasks.
6. No profile is selected from keywords, journal names, file paths, or Paper
   IDs.

A future classifier may recommend profiles, but human or workflow confirmation
must persist the chosen profile before extraction.

## 9. Inheritance and Composition

Phase 7.1 allows single inheritance only. For example:

```text
core.scientific_paper
  -> semiconductor.base
      -> semiconductor.ga2o3.photodetector
```

Multiple inheritance and unbounded deep merge are rejected because they make
the effective schema and validators difficult to audit.

Merge behavior is explicit:

- scalar identity fields cannot be inherited accidentally;
- maps may add new keys;
- replacing a parent key requires an `override` declaration;
- ordered task lists are merged by `task_id` with duplicate rejection unless
  an override is declared;
- Evidence requirements may be strengthened but not weakened by a child;
- cost limits may be lowered freely; raising them requires an explicit override;
- profile resolution emits one canonical effective manifest for provenance.

## 10. Semiconductor Profile Migration

### 10.1 Assets to Migrate

The initial profile owns the current domain assets:

- `schema.yaml`;
- `parameter_schema.yaml`;
- `material_device_schema.yaml`;
- `performance_schema.yaml`;
- `mechanism_schema.yaml`;
- parameter/material/device/performance/mechanism prompts;
- Evidence selector keyword weights and section priorities;
- summary structure expectations;
- parameter warning ranges;
- performance keyword-consistency rules;
- unit, Evidence, page, source-type, confidence, and review-status policies.

Universal rules remain outside the profile:

- payload and field-type validation primitives;
- Evidence ID resolution;
- 1-based page validation;
- source type and source reference presence;
- null preservation;
- unknown-field rejection according to the selected schema;
- atomic writes and immutable raw model responses.

### 10.2 Migration Sequence

1. Add profile manifest schemas and a loader without changing existing
   extraction entry points.
2. Register `semiconductor.ga2o3.photodetector@1.0.0` and make it reference the
   existing Ga2O3 assets.
3. Express existing selector and validator constants as profile-owned rule
   assets; compare the effective configuration against current constants.
4. Adapt one mock-only task at a time to consume `TaskProfile` while retaining
   the old public function/class behavior.
5. Switch P001 orchestration through an explicit v0.1 compatibility resolver.
6. Move schema/prompt files to canonical profile paths only after golden tests
   pass; retain old-path aliases for v0.1 readers.
7. Remove duplicated constants only after all P001 outputs and test semantics
   are equivalent.

No migration step reruns MinerU or overwrites existing P001 knowledge.

## 11. P001 v0.1.0 Compatibility Contract

P001 compatibility is non-negotiable for Phase 7.1.

The compatibility layer must preserve:

- existing Paper ID and directory layout;
- `summary.md`, `device_parameters.yaml`, `performance.yaml`, and
  `mechanism.yaml` paths;
- current YAML/Markdown output structures and domain IDs;
- Evidence IDs, one-based pages, element/source references, and quotes;
- prompt/response/run provenance filenames;
- null fields and unknown-field rejection;
- current warnings and `review_required` behavior;
- Paper Object 1.0 assembly and its four knowledge keys;
- current chunk IDs and retrieval behavior;
- all v0.1.0 tests.

The generic loader must not contain `if paper_id == "P001"` or a Ga2O3 default.
Compatibility selection belongs in a repository-owned mapping or an explicit
Registry migration:

```yaml
paper_id: P001
domain_profile:
  profile_id: semiconductor.ga2o3.photodetector
  profile_version: "1.0.0"
compatibility:
  paper_object_schema: "1.0"
  artifact_layout: p001_v0_1
```

Existing Registry files that lack these fields remain readable during the
migration window. The compatibility resolver may supply the legacy project
profile at the application composition root, where the choice is visible and
testable. The low-level profile loader must still require an explicit ID.

## 12. Validation Architecture

Validation is split into three layers.

### Layer 1 — Universal Structural Validation

- manifest/schema well-formedness;
- expected mapping/list/scalar types;
- required and unknown fields;
- null policy;
- output path containment;
- unique task, artifact, and policy IDs.

### Layer 2 — Universal Evidence Validation

- every populated claim resolves to an Evidence record;
- page is 1-based and agrees with Evidence;
- source type agrees with Evidence;
- source reference exists;
- model output cannot create unknown Evidence IDs;
- validation never rewrites the model response.

### Layer 3 — Domain Semantic Validation

- task-specific units and measurement rules;
- parameter warning ranges;
- Evidence keyword consistency;
- expected summary sections;
- allowed confidence/review policies;
- optional terminology or ontology checks.

Layer 3 emits warnings and review requirements unless a violation makes the
artifact structurally invalid. It must not fabricate, normalize, or “correct” a
scientific result silently.

## 13. Security and Reproducibility

The loader must enforce:

- all referenced local assets resolve under approved repository roots;
- no `..` traversal, absolute paths, network URLs, or symlink escape;
- YAML safe loading only;
- no arbitrary Python import or expression evaluation from profile data;
- exact version pinning for parents and policies;
- deterministic canonicalization and fingerprinting;
- clear failure before LLM calls on missing assets or unknown policies;
- provenance records containing profile ID, version, fingerprint, task version,
  schema version, prompt fingerprint, and validator policy versions.

Profile data must never contain API keys. LLM credentials remain exclusively in
the provider adapter environment.

## 14. Future Domain Examples

The framework must support these shapes without changing generic core code:

### Battery

- materials and cell chemistry;
- electrode/electrolyte/separator composition;
- cell format and test protocol;
- capacity, energy density, rate, Coulombic efficiency, cycle life;
- degradation mechanism and measurement conditions.

### Catalysis

- catalyst composition and preparation;
- reaction, reactants, products, solvent, temperature, pressure, time;
- conversion, yield, selectivity, turnover metrics;
- active-site and kinetic/mechanistic claims.

### Biomedical

- study design, population, intervention/exposure, comparator, and outcomes;
- sample size, timepoint, effect estimate, uncertainty, and adverse events;
- statistical methods, preregistration, and risk-of-bias fields;
- stronger review policy and explicit non-clinical-use metadata.

These examples prove the manifest needs arbitrary task/artifact sets. They are
not schemas to be guessed or implemented during the Ga2O3 migration.

## 15. Test Strategy

Phase 7.1 implementation should add tests in this order:

1. valid profile and catalog loading;
2. missing/unknown field rejection;
3. path traversal, absolute path, URL, and unknown policy rejection;
4. parent resolution, cycle rejection, and deterministic override behavior;
5. stable canonical fingerprinting;
6. task/artifact collision detection;
7. profile-driven mock extraction with no API call;
8. universal Evidence validation shared across two synthetic profiles;
9. Ga2O3 effective-profile equivalence with current schemas/rules;
10. P001 golden compatibility for artifacts, warnings, Paper Object, chunks,
    and Registry behavior;
11. one minimal synthetic non-semiconductor profile that requires no generic
    source-code conditional.

Real battery, catalysis, biomedical, or DeepSeek calls are excluded from the
Phase 7.1 test gate.

## 16. Implementation Slices

### 7.1-A — Contracts and Loader

Add immutable profile/task/artifact models, catalog resolution, safe loading,
inheritance validation, fingerprints, and unit tests. No existing pipeline uses
the loader yet.

### 7.1-B — Semiconductor Compatibility Profile

Register the current Ga2O3 schemas and rules as
`semiconductor.ga2o3.photodetector@1.0.0`. Add equivalence tests against current
constants and P001 output contracts.

### 7.1-C — Generic Task Adapter

Adapt mock-only extraction, selector, validator, and writer orchestration to a
TaskProfile. Preserve existing classes as compatibility facades.

### 7.1-D — Registry Selection

Add optional profile identity/version fields and migrate P001 explicitly.
Reconcile lifecycle metadata without changing Parser, RAG, or VectorStore
semantics.

Each slice must leave the full test suite green and may be committed
independently. No slice should combine profile abstraction with Paper Object
2.0 or production embedding work.

## 17. Acceptance Criteria

Phase 7.1 is complete when:

1. profile selection is explicit and version-pinned;
2. generic loaders have no implicit Ga2O3 or P001 default;
3. the Ga2O3 schemas and semantic rules are owned by one semiconductor profile;
4. profile manifests cannot execute arbitrary code or escape approved paths;
5. a generic mock task runs from a profile without editing field-name constants;
6. one synthetic alternate-domain profile loads and validates through the same
   interfaces;
7. P001 v0.1.0 artifacts, Evidence traceability, Paper Object 1.0, chunks, and
   tests remain compatible;
8. Parser, RAG, and VectorStore core behavior is unchanged;
9. no real LLM API call is required for the acceptance suite;
10. profile and task fingerprints are recorded in new-run provenance.

## 18. Decisions Required Before Coding

The following decisions should be accepted before Phase 7.1-A begins:

1. Use repository-owned YAML profiles with trusted policy IDs, not executable
   plugins.
2. Allow only single, pinned inheritance in profile schema 1.0.
3. Keep profile version separate from task and output schema versions.
4. Make domain selection explicit through Registry or pipeline input.
5. Preserve the current Ga2O3 files initially and migrate paths only after
   equivalence tests.
6. Treat P001 compatibility as an application-level mapping, not a generic
   loader default.
7. Defer Paper Object 2.0 and RAG metadata filters to subsequent approved
   phases.

This design creates a narrow, auditable abstraction seam: stable scientific
facts below it, configurable domain knowledge above it.
