# Phase 7 Architecture Review

## 1. Review Scope

This review evaluates v0.1.0 at commit
`bd9f167` as the starting point for evolving Ga2O3 Paper Learning System into a
general AI scientific-paper learning system. It is an architecture assessment,
not an implementation specification. No Phase 7 code is introduced here.

The review follows five paths:

1. schemas and domain contracts;
2. extraction, prompting, and validation;
3. the Paper Object knowledge boundary;
4. Registry and batch lifecycle management;
5. Embedding, Vector Store, and evidence-aware retrieval.

The central invariant remains unchanged: Unified Document plus Evidence is the
factual source of truth. Domain knowledge is a derived, reviewable layer.

## 2. Executive Assessment

v0.1.0 is a strong single-domain vertical slice, not yet a domain-neutral
knowledge platform. Its lower layers are already broadly reusable:

- ingestion and bibliographic metadata;
- parser adapters and Unified Document Schema;
- Evidence IDs, pages, locators, and source traceability;
- provider-neutral LLM adapters;
- local vector-store interfaces and evidence-aware retrieval results.

The main coupling begins above Evidence. The intended **Core Schema + Domain
Extension** design exists, but the implementation also encodes the initial
Ga2O3 photodetector profile in Python constants, keyword selectors, validators,
fixed filenames, Paper Object sections, and P001-only orchestration. A second
domain can be represented today only by adding schemas *and* editing reusable
code. That is the defining abstraction gap for Phase 7.

The recommended strategy is evolutionary: retain the stable fact, metadata,
storage, and provider layers; introduce a versioned Domain Profile boundary;
then migrate extraction, validation, Paper Object assembly, and chunking to
consume that boundary. A full parser or RAG rewrite is not justified.

## 3. Current Architecture Evaluation

| Layer | Current evaluation | Domain portability |
| --- | --- | --- |
| Ingestion | Stable paper discovery, IDs, folders, and metadata association | High |
| Metadata | DOI, authors, year, journal, BibTeX/RIS normalization | High, with future identifier extensions |
| Parser | MinerU adapter, tables, figures, equations, sections, and pages converge on Unified Document | High |
| Evidence | One-based pages, source references, element types, quotes, and IDs are preserved | High |
| Core Knowledge | Research problem, methodology, results, innovation, limitations, and evidence traceability | High |
| Domain Knowledge | Ga2O3 schemas are explicit and evidence-aware | Low outside semiconductor devices |
| Extraction | Good bounded prompts and provenance, but selectors and orchestration are task/P001 specific | Low to medium |
| Validation | Strong evidence closure; several structural and semantic checks are photodetector-specific | Medium |
| Paper Object | Useful validated aggregate with 100% evidence closure | Medium-low because knowledge slots are fixed |
| Registry/Batch | Mostly discipline-neutral lifecycle tracking | Medium-high; missing domain/profile identity |
| Embedding | Generic chunk record and adapter contract | Medium; chunk traversal assumes four fixed knowledge groups |
| Vector Store | Generic local FAISS boundary | High |
| Retrieval | Evidence-aware, model-neutral result contract | High at interface level; limited filtering and evaluation |

Overall, v0.1.0 should be treated as a validated domain pack plus a reusable
core, rather than as a monolithic Ga2O3 application that must be renamed and
rewritten.

## 4. Ga2O3 Specialization Inventory

### 4.1 Schema

The explicit domain pack is correctly isolated under
`data/domains/semiconductor/ga2o3/`, but its contracts are also duplicated in
code.

Current specialization points:

- `schema.yaml` declares `semiconductor.ga2o3.photodetector` and fields for
  material, phase, doping, substrate, device structure, fabrication, optical
  and electrical performance, mechanism, and comparison.
- `parameter_schema.yaml`, `material_device_schema.yaml`,
  `performance_schema.yaml`, and `mechanism_schema.yaml` subdivide the same
  domain into task-specific contracts.
- `src/knowledge/schema.py` defaults to the Ga2O3 domain schema even though the
  loader can accept another path.
- The parameter, material/device, performance, and mechanism schema modules
  hard-code both the Ga2O3 schema paths and expected field names in Python.
- Core `data/papers/TEMPLATE/knowledge/core.yaml` and
  `domain.yaml` are appropriately domain-neutral.

Required abstraction: a versioned Domain Profile should own schema paths,
field groups, task definitions, outputs, selectors, and validator policies.
Generic loaders should not have a Ga2O3 default; the selected profile should
come from the paper record or explicit pipeline configuration.

### 4.2 Extraction and Validation

The model-independent `KnowledgeExtractor`, `ExtractionContext`, and LLM
adapter boundary are reusable. The concrete extraction stack is specialized in
several ways:

- `P001SummaryExtractor`, `P001MaterialDeviceExtractor`, performance extraction,
  and mechanism extraction reject documents whose ID is not `P001`.
- Parameter/performance/mechanism fields are compiled into Python constants,
  so changing a YAML schema does not change the accepted response contract.
- Evidence selectors use English photodetector/device keywords such as Ga2O3,
  responsivity, detectivity, photocurrent, electrode, substrate, band alignment,
  and carrier transport.
- Negative keyword lists encode boundaries between fabrication, performance,
  and mechanism that are specific to the current device workflow.
- `PromptStrategyRegistry` is fixed to summary, parameter, and mechanism
  strategies; performance and material/device use parallel custom paths rather
  than one task registry.
- `parameter_prompt.md` assumes device and material parameters.
- Summary quality requires Material/System, Device Structure, Mechanism, and
  Performance sections. Those are not universal scientific-summary sections.
- Parameter anomaly checks assume wavelength, responsivity, detectivity,
  response time, and on/off ratio.
- Performance semantic consistency checks know four photodetector metrics.
- Writers and provenance manifests use fixed device/performance/mechanism
  filenames and task names.

Required abstraction: retain generic evidence binding, page/source validation,
null preservation, unit handling, confidence, and review status. Move field
sets, keyword/scoring policies, section expectations, semantic checks, prompt
templates, and output names into Domain Profile task specifications.

### 4.3 Knowledge Object

The Core Knowledge model is portable, but Paper Object 1.0 is not fully
extension-oriented.

Current specialization points:

- `data/paper_object/schema.yaml` requires exactly `summary`, `parameters`,
  `performance`, and `mechanism` under `knowledge`.
- `PaperObjectBuilder.KNOWLEDGE_FILES` requires `summary.md`,
  `device_parameters.yaml`, `performance.yaml`, and `mechanism.yaml`.
- The builder understands device/performance/mechanism run-report filenames and
  inspects the internal `mechanisms` structure for review warnings.
- Summary Evidence is reconstructed by parsing the JSON payload embedded after
  `Extraction task:` in a prompt provenance file. This binds the object builder
  to one prompt serialization format.
- `PaperObjectChunker.GROUPS` repeats the same four fixed knowledge groups.
- Evidence IDs are recognized through the project-specific `E` plus five-digit
  regular expression instead of a declared Evidence-ID contract.

Required abstraction: Paper Object 2.0 should have stable core sections and a
map or list of versioned knowledge artifacts, each carrying `domain_id`,
`task_id`, `schema_version`, payload, provenance, validation status, and
Evidence references. A v0.1 compatibility reader must preserve the existing
four keys for P001.

### 4.4 Registry and Batch Lifecycle

Registry fields for identity, metadata, paths, and most lifecycle stages are
domain-neutral. The following gaps block reliable profile selection:

- Paper records have no `domain_id`, Domain Profile version, knowledge schema
  version, or enabled extraction task list.
- `processing_status` is represented differently between the historical
  registry design and current record usage, which needs an explicit migration
  rule rather than inference.
- `vectorstore_status` exists in `registry.yaml` but is absent from
  `LIFECYCLE_FIELDS`; RegistryManager therefore cannot update or query it through
  the normal lifecycle API.
- Batch execution receives a generic `knowledge_executor`, but no configured
  domain/task plan exists for selecting the right extractor set.
- Artifact readiness assumes the current fixed knowledge filenames.

Required abstraction: extend records additively with profile identity and
schema/task versions. Make lifecycle stages internally consistent, and let
batch planning resolve tasks from the profile rather than from filenames.

### 4.5 Embedding, Vector Store, and RAG

The vector record, FAISS store, query encoder injection, retrieval result, and
Evidence-ID preservation do not contain Ga2O3 vocabulary. They should remain
generic.

The coupling is upstream:

- PaperObjectChunker traverses exactly summary, parameters, performance, and
  mechanism.
- Chunk IDs encode those fixed group names.
- The summary chunker depends on Markdown lines containing embedded Evidence
  IDs, while structured chunks depend on `evidence_id` or `evidence_refs` at
  particular nesting levels.
- Retrieval exposes paper, chunk, score, Evidence IDs, and source, but not
  domain, task, page, element type, schema version, or metadata filters.
- v0.1.0 uses deterministic mock vectors, so cross-domain semantic retrieval
  support has not been evaluated.

Required abstraction: make chunking artifact-driven and carry typed metadata
from the Paper Object. Keep VectorStore and Retriever interfaces stable while
adding optional filters and richer result metadata. Do not put domain logic in
FAISS or the base retriever.

## 5. Modules Requiring Domain Abstraction

| Priority | Module or contract | Why it requires abstraction | Recommended boundary |
| --- | --- | --- | --- |
| Critical | `src/knowledge/schema.py` defaults | Generic loader selects Ga2O3 implicitly | Explicit Domain Profile selection |
| Critical | Four Ga2O3 task schema modules | YAML contracts are duplicated as Python constants | Schema-driven field/group compilation |
| Critical | Material/device, performance, and mechanism extractors | Hard-coded P001 checks, keywords, task shapes, and merge rules | Generic task executor plus profile task specification |
| Critical | Paper Object schema/builder | Four fixed knowledge keys and filenames | Versioned artifact collection with a v1 compatibility view |
| High | Summary quality and parameter/performance validators | Device-specific required sections, ranges, and keyword checks | Core validators plus profile-supplied semantic rules |
| High | Batch status/readiness | Knowledge completion is inferred from fixed files | Profile task manifest and artifact readiness policy |
| High | Embedding chunker | Fixed knowledge groups and Evidence-ID regex | Generic artifact visitor and declared Evidence contract |
| High | Registry schema | Cannot select or audit a domain profile | Add domain/profile/schema/task metadata |
| Medium | Prompt strategy registry | Fixed enum and incomplete convergence of task types | Runtime task registry loaded from profiles |
| Medium | Writers/run manifests | Output names and task identifiers are fixed | Common artifact/provenance envelope |
| Medium | RAG response/filter model | No domain/task/schema/page filtering | Optional typed metadata and filter object |
| Low | Package names and top-level documentation | Product identity still says Ga2O3 | Rename only after compatibility and migration contracts stabilize |

## 6. Cross-Domain Expansion Assessment

### 6.1 Semiconductor Papers

**Readiness: medium-high.**

The existing material, device, fabrication, electrical performance, optical
performance, and mechanism vocabulary transfers well to adjacent semiconductor
devices. Unified Figures, Tables, Equations, and Evidence are already suitable.

Main gaps:

- current field sets favor photodetectors and optoelectronic memories;
- transistor, power-device, photovoltaic, LED, sensor, and integrated-circuit
  metrics need separate task schemas;
- selectors must be profile-specific rather than one growing keyword list;
- unit normalization and conditions need a reusable measurement ontology.

This is the best second-domain family for validating the abstraction because it
maximizes reuse without hiding the current coupling.

### 6.2 Materials-Science Papers

**Readiness: medium.**

Core claims, methodology, results, material composition, phase, defects,
fabrication, Tables, Figures, and Evidence transfer well. The fixed device and
photodetector performance slots do not.

Needed domain concepts include synthesis route, processing history,
microstructure, morphology, characterization method, thermodynamic/mechanical/
optical/electrical properties, sample identity, and measurement conditions.
The schema must distinguish a material specimen from a device and allow repeated
sample-condition-result observations.

### 6.3 Chemistry Papers

**Readiness: low-medium.**

The parser, bibliographic metadata, Core Knowledge, Evidence, Tables, and
general LLM boundary remain useful. Chemistry needs a substantially different
extension for compounds, identifiers, reactions, stoichiometry, catalysts,
solvents, temperature/time/pressure, yield/selectivity, analytical methods, and
spectroscopic characterization.

Chemical structures, reaction schemes, and compound identity resolution are
not represented by the current Unified Document or domain schema beyond generic
Figures/Equations. Phase 7 should not claim chemistry-grade structure extraction
until those loss and normalization boundaries are benchmarked.

### 6.4 Biomedical Papers

**Readiness: low.**

The Evidence-first core is valuable, but the current knowledge taxonomy is not
sufficient for biomedical evidence. Required concepts include study design,
population, eligibility, intervention/exposure, comparator, outcomes,
timepoints, sample size, effect estimates, confidence intervals, adverse
events, statistical methods, preregistration, and risk of bias.

Biomedical expansion also requires stricter distinction between author claims
and system interpretation, domain terminology normalization, retraction/version
awareness, and explicit non-clinical-use safeguards. It should follow, not lead,
the Domain Profile refactor.

## 7. Technical Debt

1. **Configuration/code duplication.** The same domain field contracts appear
   in YAML and Python, creating drift risk.
2. **Single-paper restrictions inside reusable classes.** P001 safeguards were
   correct for first real calls but now prevent batch/domain reuse.
3. **Parallel task frameworks.** Summary, parameter, material/device,
   performance, and mechanism evolved independently and do not share one task
   specification or orchestration contract.
4. **Fixed artifact topology.** Completion, Paper Object assembly, validation,
   and embedding depend on known filenames and four knowledge groups.
5. **Prompt-provenance parsing.** Evidence reconstruction depends on parsing a
   prompt string rather than consuming a stable structured provenance artifact.
6. **Mixed generic and semantic validation.** Evidence closure is reusable;
   domain keyword/range policies are embedded beside it.
7. **Registry lifecycle mismatch.** `vectorstore_status` is data-visible but not
   part of the manager's lifecycle fields.
8. **No schema migration contract.** Domain schema 1.0 and Paper Object 1.0 lack
   explicit compatibility/migration rules.
9. **Cross-domain test gap.** Nearly all end-to-end evidence comes from P001 and
   semiconductor/table benchmarks; no synthetic contract fixture proves that a
   new domain can be added without editing core modules.
10. **Retrieval quality gap.** Mock vectors prove wiring and traceability, not
    semantic quality within or across disciplines.

## 8. Phase 7 Modification Priorities

### P0 — Freeze Core Contracts and Define the Domain Profile

- Freeze Unified Document, Evidence, metadata, LLM adapter, vector-store, and
  retrieval-result contracts as the stable base.
- Define a small versioned Domain Profile manifest containing domain identity,
  schema references, task IDs, prompt/selector/validator policies, output
  artifacts, and chunking metadata.
- Register the existing Ga2O3 photodetector behavior as the first compatibility
  profile without changing its scientific outputs.
- Add synthetic contract fixtures for semiconductor, materials, chemistry, and
  biomedical profiles before migrating real pipelines.

Success criterion: selecting a domain is explicit and there is no implicit
Ga2O3 default in generic code.

### P1 — Make Extraction and Validation Schema-Driven

- Replace Python field/group constants with compiled task contracts from the
  selected profile.
- Converge the parallel extractors on one bounded Evidence → prompt → response
  → validate → provenance pipeline.
- Separate universal validation from optional domain-semantic checks.
- Remove P001 restrictions from reusable components while keeping P001 scripts
  as explicit single-paper entry points.

Success criterion: a new task/schema can run in mock mode without editing the
generic extractor, validator, or writer source.

### P2 — Introduce Paper Object 2.0 with Compatibility

- Preserve identity, source Evidence index, aggregate validation, and review
  status.
- Represent knowledge as versioned artifacts rather than four required domain
  slots.
- Store structured provenance directly instead of reverse-parsing prompt text.
- Provide a deterministic v1 reader/migration view so P001 and existing tests
  remain valid.

Success criterion: the object can carry arbitrary domain tasks while every
claim still resolves to Evidence.

### P3 — Make Registry, Batch Planning, and Chunking Profile-Aware

- Add domain/profile/schema/task version fields to Registry records.
- Reconcile `vectorstore_status` with the lifecycle manager.
- Plan batch work from profile tasks and artifact state.
- Traverse Paper Object artifacts generically and attach domain/task/schema/page
  metadata to chunks.

Success criterion: two papers with different profiles can share one Registry,
batch report, vector store, and retriever without filename conditionals.

### P4 — Cross-Domain Evaluation and Retrieval Quality

- Add per-domain benchmark fixtures and Evidence-coverage metrics.
- Evaluate a real, versioned embedding model separately from the architecture
  refactor.
- Add optional metadata/domain/task filters and retrieval evaluation.
- Establish biomedical safety and chemistry-structure limitations before making
  domain-specific quality claims.

Success criterion: retrieval quality and traceability are reported independently
for each domain; a high score in one domain is not presented as universal.

## 9. Stable Modules Not Recommended for Redesign

The following modules should be extended through adapters or metadata, not
rewritten during Phase 7:

- Unified Document Schema and the one-based page convention;
- Evidence records, source references, raw locators, and Evidence closure;
- MinerUAdapter v2 and its legacy fallback;
- parser table-recovery boundaries and existing benchmark layers;
- RIS/BibTeX metadata ingestion and normalization core;
- paper directory/ID ingestion mechanics;
- `LLMAdapter`, `DeepSeekLLMAdapter`, and mock-adapter contracts;
- `EmbeddingAdapter` and `EmbeddingChunk` minimum evidence-linked contract;
- FAISS store and generic VectorStore interface;
- Retriever injection of a query encoder and evidence-aware result identity;
- atomic YAML/JSON writing patterns and review-required semantics;
- existing P001 outputs and v0.1.0 golden tests as compatibility fixtures.

These modules may receive additive fields or wrappers, but changing their
meaning would create migration risk without solving the domain-abstraction
problem.

## 10. Recommended Target Boundary

```text
Scientific Source
  -> Ingestion + Metadata
  -> Parser Adapter
  -> Unified Document + Evidence                 [stable core]
  -> Domain Profile Resolver                     [new boundary]
  -> Generic Task Extraction + Core Validation   [profile-driven]
  -> Versioned Knowledge Artifacts
  -> Paper Object 2.0 + Evidence Index
  -> Generic Chunking + Embedding + Vector Store
  -> Evidence-aware Retrieval with filters
```

A Domain Profile supplies vocabulary and task policy; it must not replace the
Unified Document, create a second Evidence system, choose an LLM provider, or
write directly to the vector store.

## 11. Phase 7 Entry Criteria

Phase 7 implementation should begin only when the following decisions are
explicitly accepted:

1. Domain Profile manifest shape and versioning policy.
2. Paper Object 1.0 compatibility and 2.0 migration policy.
3. Registry additions and lifecycle reconciliation.
4. Separation between universal validators and domain-semantic rules.
5. A second-domain pilot; an adjacent semiconductor or general materials
   profile is recommended before chemistry or biomedical work.
6. Cross-domain acceptance tests that require no real LLM API call.

The architecture is suitable for generalization, but the safe path is to make
the knowledge layer pluggable while keeping the evidence-first core stable.
