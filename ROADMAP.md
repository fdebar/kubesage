# KubeSage Roadmap & Project History

> **Status:** reconstructed from the Git history of `fdebar/kubesage` and the project's documented development history.
>
> **Important:** KubeSage has historically been developed directly on `main`; there are no formal sprint branches that can be used as authoritative boundaries. The sprint numbers below therefore distinguish between **explicitly known sprint milestones** and **functional phases reconstructed from commit history**. Where the exact sprint number cannot be proven from Git, the roadmap deliberately uses a phase instead of inventing one.

---

# 1. Project Vision

KubeSage is an AI-assisted Kubernetes incident analysis platform.

Its core philosophy is:

> **Deterministic evidence first, AI reasoning second.**

KubeSage collects operational evidence from Kubernetes and the observability stack, applies deterministic diagnostics and correlation, builds incident context, then gives a constrained and structured context to an LLM for explanation and recommendations.

The product has evolved from a Kubernetes diagnostic engine into an incident-intelligence platform covering:

* Kubernetes resources and events
* container lifecycle and pod behaviour
* Prometheus metrics and resource usage
* Loki application/container logs
* Tempo distributed traces
* OpenTelemetry instrumentation
* deterministic diagnostic rules
* finding correlation
* incident timelines
* incident intelligence / root-cause candidates
* structured AI reports
* AI report quality evaluation and evidence grounding
* persistent analysis history
* automatic incident detection through a watcher
* web UI and Grafana integration
* GitOps deployment

---

# 2. Evolution at a Glance

```text
Kubernetes diagnostic CLI
        │
        ▼
Deterministic diagnostic engine
        │
        ├── Kubernetes resources/events
        ├── Diagnostic rules
        └── Findings + evidence
        │
        ▼
Prometheus enrichment
        │
        ▼
Loki + Tempo + OpenTelemetry
        │
        ▼
Finding correlation
        │
        ▼
Persistent incident analysis
        │
        ▼
Automatic incident detection
        │
        ▼
Incident Timeline
        │
        ▼
Incident Intelligence
        │
        ▼
AI Context / Evidence Grounding
        │
        ▼
Structured AI Report
        │
        ▼
AI Quality Evaluation
        │
        ▼
Web UI + operational observability
```

The major architectural transition is from:

> **"Detect a Kubernetes problem."**

to:

> **"Reconstruct and explain an incident from multiple independent evidence sources."**

---

# 3. Reconstructed Development History

## Phase 1 — Kubernetes Diagnostic Foundation

**Period:** July 2026

The project started as a Kubernetes-focused diagnostic engine.

Key milestones visible in Git history:

* Kubernetes service introduced.
* Container-oriented diagnostic rules added.
* Findings model introduced.
* Rule tests added.
* Dynamic rule discovery and rule-management CLI introduced.
* Finding categories and evidence fields added.
* FastAPI interface introduced.
* Kubernetes deployment/containerisation added.
* Stronger typing and null handling progressively introduced.

Representative commits:

* `cac482a8` — `feat: add kubernetes service`
* `8d6ea6b3` — `feat: add rules for containers`
* `669bdd38` — `feat: add findings and their rules`
* `3c103d5d` — `feat: implement dynamic rule discovery and add command-line interface for rule management`
* `877d929e` — `feat: add category and evidence fields to Finding model and implement five new analysis rules`
* `eb6953f3` — `feat: implement FastAPI interface with structured schemas, exception handling, and decoupled Kubernetes client utility`
* `db78a729` — `feat: containerize application and implement Kubernetes deployment configuration with in-cluster authentication support`

### Architectural outcome

KubeSage acquired its first stable separation between:

```text
Kubernetes collection
        ↓
Diagnostic rules
        ↓
Findings
        ↓
API / CLI
```

This is the foundation on which the later AI architecture was built.

---

## Phase 2 — Diagnostic Engine Maturation

**Period:** July 20–28, 2026

The rule system became a real diagnostic engine rather than a collection of ad-hoc checks.

Rules and concepts added or redesigned include:

* CrashLoop / restart analysis
* ImagePull-related availability analysis
* readiness failures
* Pending / scheduler diagnostics
* OOMKilled detection
* memory pressure
* CPU throttling
* rule categories
* rule IDs
* priorities
* finding kinds
* structured evidence
* recursive/dynamic rule discovery

An important design reset occurred when existing rules were deliberately removed and the availability-analysis strategy was reconsidered.

Representative commits:

* `e985e423` — rules removed to rethink the strategy
* `81b3c349` — availability analysis redesigned around CrashLoop, ImagePull and restarts
* `85ccf20e` — Readiness analyzer
* `1a4b25d2` — PendingRule and rule categories
* `7e7d1462` — OOMKilledRule
* `577fc109` — memory pressure rule
* `ecc0785e` — CPU throttling rule
* `301650f1` / `cb639d23` — standardisation around `rule_id`

### Architectural outcome

The diagnostic engine became:

```text
Rule discovery
     ↓
Rule evaluation
     ↓
Structured Finding
     ├── rule_id
     ├── category
     ├── severity
     ├── priority
     ├── kind
     └── evidence
```

This structured finding model later became critical for correlation and AI grounding.

---

## Phase 3 — Prometheus & Resource Intelligence

**Period:** July 21–August 2026

Prometheus was introduced as a first-class evidence source.

Capabilities progressively added:

* Prometheus service integration
* resource-usage models
* incident metric collection
* filesystem usage
* per-container CPU/memory usage
* CPU throttling metrics
* resource-limit enrichment
* concurrent metric collection
* connection pooling
* worker metrics
* custom KubeSage Prometheus metrics

Representative commits:

* `92d7f030` — Prometheus metrics collection integrated
* `87eb7cce` — Prometheus integrated into incident analysis
* `aa81a27d` — modular Prometheus queries and incident metric snapshots
* `d5424a1b` — filesystem usage
* `09ae46ff` — CPU throttling metrics
* `b9fa7ae3` — per-container CPU/memory usage
* `5f6a4e19` — resource-limit enrichment
* `78c0aa38` — connection pooling
* `a69727fa` — concurrent metric collection

### Architectural outcome

KubeSage stopped reasoning only from Kubernetes state and began reasoning from:

> **state + measured runtime behaviour**

---

## Phase 4 — Observability Platform: Prometheus, Loki, Tempo

**Period:** July–August 2026

The project evolved from a diagnostic API into a self-observable platform.

The observability stack introduced:

* Prometheus
* Loki
* Tempo
* Grafana
* OpenTelemetry
* Grafana Alloy

Loki became a first-class incident evidence source, allowing KubeSage to inspect logs alongside Kubernetes and metrics data.

Representative commits:

* `d3552faa` — observability stack with Grafana, Loki and Tempo
* `5c96fbe7` — Loki service integrated into incident analysis
* `cd4688dd` — Loki tenant/request handling
* `35ec4a3d` — Loki tracing/error handling and tests
* `3042e757` — Loki availability checks

The observability configuration was progressively made optional and configurable so KubeSage could operate with different combinations of providers.

### Architectural outcome

```text
Kubernetes ─────┐
Prometheus ─────┼──→ Incident Builder
Loki ───────────┤
Tempo ──────────┘
```

The incident model became inherently multi-source.

---

## Phase 5 — Finding Correlation

**Period:** July 28 – August 2026

A key conceptual milestone was the introduction of finding correlation.

Instead of treating every rule result as an independent problem, KubeSage began identifying relationships between findings.

Capabilities added:

* correlation engine
* correlation rules
* structured relationship evidence
* input/relationship metadata
* correlation CLI
* deduplication of correlated findings
* OpenTelemetry instrumentation of correlation

Representative commits:

* `4b49b0a4` — finding correlation engine
* `44887a57` — evidence source tracking and AI-context helpers
* `188f8eff` — structured correlation evidence
* `bb425b8b` — correlations CLI
* `29a3aeb8` — relationship metadata and memory-exhaustion diagnosis test
* `e4b082b6` — correlation tracing

### Architectural outcome

The engine progressed from:

```text
Finding A
Finding B
Finding C
```

to:

```text
Finding A ──┐
            ├──→ Correlated incident hypothesis
Finding B ──┘
```

This was one of the most important prerequisites for useful AI reasoning.

---

## Phase 6 — Persistence & Analysis API

**Period:** August 2026

KubeSage gained persistent incident analyses and a more complete application architecture.

Key changes:

* structured database models
* migrations
* structured evidence/recommendation persistence
* paginated analysis history
* database indexes
* PostgreSQL support
* Helm integration
* database health/readiness checks
* separation of application initialisation concerns

Representative commits:

* `47ed95e3` — structured evidence/recommendation models and migrations
* `b0426ccd` — analysis indexes and paginated analysis listing
* `ce247483` — PostgreSQL migration and Helm integration
* `092a4016` — database health check
* `c18ffaf3` — database-aware readiness handling

### Architectural outcome

KubeSage became a persistent service rather than a stateless diagnostic endpoint.

```text
Incident
   ↓
Analysis
   ├── findings
   ├── evidence
   ├── recommendations
   └── AI report
   ↓
PostgreSQL
```

---

## Phase 7 — Automatic Incident Detection / Watcher

**Period:** August 4–11, 2026

KubeSage gained proactive incident detection.

The Kubernetes pod watcher can observe pod/container behaviour and trigger analysis when failures occur.

Capabilities added:

* pod watcher
* event-source abstraction
* retry/error recovery
* pod state cache
* state diffing
* initial cache population
* watcher metrics
* worker Prometheus endpoint

Representative commits:

* `2406c05f` — Kubernetes pod watcher
* `189793a3` — EventSource abstraction and reliability improvements
* `059d3a01` — stream recovery/retries and tests
* `c6ffecb3` — pod state caching/diffing
* `fbbf5afd` — watcher observability metrics
* `6f60a785` — cache initialisation from current cluster state

### Architectural outcome

KubeSage changed from:

> **"Ask me to analyse this pod."**

to:

> **"Watch the cluster and start an investigation when something changes."**

This is the foundation of the proactive SRE direction.

---

# 4. Explicit Sprint Milestones

The following milestones correspond to sprint numbers that are known from the project's development history.

Earlier work is intentionally represented as functional phases above because exact sprint boundaries are not encoded in Git.

---

## Sprint 14 — OpenTelemetry & Analysis Tracing

**Status:** Completed

OpenTelemetry became a core architectural concern rather than an afterthought.

The project added:

* OpenTelemetry trace context propagation
* trace/span IDs in structured logging
* instrumentation of Kubernetes collection
* instrumentation of Prometheus/Loki operations
* DiagnosticEngine rule spans
* correlation spans
* end-to-end analysis tracing
* integration tests for trace completeness

Representative commits:

* `ec84fed2` — trace context propagation
* `d3c7d035` — trace/span IDs in logs
* `0d064c28` — Kubernetes collection tracing
* `7e170616` — DiagnosticEngine rule spans
* `d932ae67` / `35ec4a3d` — Loki tracing
* `e4b082b6` — correlation tracing

The resulting analysis trace is conceptually:

```text
analysis.execute
├── analysis.incident.collect
├── analysis.rules.engine.analyze
├── analysis.incident_intelligence.build
└── analysis.ai_report.generate
    └── llm.generate_report
```

---

## Sprint 17 — Incident Timeline

**Status:** Completed

The Incident Timeline introduced temporal reasoning over heterogeneous evidence.

The timeline aggregates:

* Kubernetes events
* container lifecycle events
* Prometheus metric changes / threshold observations
* Loki log events
* timestamps
* severity

Representative commits:

* `4ed8d49c` — timeline model and builder
* `a40f7b5a` — container lifecycle events
* `449f35a0` — metric threshold detection and timeline integration

### Why this milestone matters

Before the timeline, KubeSage knew:

> **what findings existed.**

After the timeline, it could reason about:

> **what happened first, what happened next, and how the incident evolved.**

---

## Sprint 18 — Incident Intelligence

**Status:** Completed / evolved further in subsequent commits

Incident Intelligence became the structured layer between raw findings and AI reasoning.

It centralises:

* findings
* correlations
* root-cause candidates
* timeline
* contextual relationships

Representative commits:

* `593a9940` — IncidentIntelligence model/builder
* `a5f78570` — IncidentIntelligence builder integrated into analysis
* `f9eeaf78` — IncidentIntelligence API schema/mapper
* `c95cd3ee` — persistent correlations and root causes
* `7f8aca90` — dedicated database models for correlations/root causes

### Architectural role

```text
Raw evidence
     ↓
Findings
     ↓
Correlations
     ↓
Root-cause candidates
     ↓
Timeline
     ↓
Incident Intelligence
```

This layer is intentionally deterministic and structured before the LLM is invoked.

---

## Sprint 19 — Application Error Detection

**Status:** Completed

KubeSage expanded beyond infrastructure symptoms to application-level failures.

The application error classifier/rule detects patterns such as:

* exceptions
* tracebacks
* HTTP 5xx responses
* connection refused
* timeouts
* database errors
* explicit error-level logs

Representative commits:

* `a12b9ba6` — application error detection rule
* `f8a22e6f` — ApplicationErrorClassifier integrated into timeline log processing
* `8a521733` — Loki error/warning processing in TimelineBuilder

### Architectural outcome

KubeSage can now connect:

```text
Infrastructure symptom
        ↓
Application error
        ↓
Temporal context
        ↓
Incident hypothesis
```

This is the beginning of true **application-aware incident intelligence**.

---

## Sprint 20 — AI Report Quality

**Status:** Completed

The project shifted from simply generating AI reports to measuring and constraining their quality.

The quality suite covers scenarios including:

* CrashLoop / unknown cause
* OOMKilled
* CPU throttling
* readiness failure
* application errors
* correlated OOM / memory exhaustion

The prompt was also strengthened around evidence-driven diagnostics.

Representative commit:

* `4ab370c1` — AI report quality suite and evidence-driven prompt instructions

The project subsequently added automated scoring and stronger evidence validation.

---

## Sprint 21 — AI Quality, Grounding & Evidence Integrity

**Status:** Completed / progressively hardened

This phase focused on reducing hallucination and ensuring that AI conclusions remain grounded in actual KubeSage evidence.

Key concepts introduced during this phase:

* automated AI quality scoring
* evidence grounding
* canonical evidence identifiers
* source attribution
* evidence uniqueness
* source/timeline consistency
* ID normalisation/validation
* ambiguous and contradictory scenarios
* model comparison / quality benchmarking
* structured `evidence_refs` in AI reports

### Architectural principle

The LLM should not be trusted merely because it produces valid JSON.

The system must also validate:

```text
Can the claim be traced to evidence?
        ↓
Is the evidence real?
        ↓
Is the source canonical?
        ↓
Is the reference unique and consistent?
```

This is a foundational part of KubeSage's anti-hallucination strategy.

---

## Sprint 22 — Productisation / Web & Platform Integration

**Status:** Historical phase reconstructed from Git; exact sprint boundary is less certain than later milestones.

During August, the project progressively acquired a complete operational/product surface:

* analysis API consolidation
* dashboard API
* live cluster metrics
* analysis reporting
* Settings/health service
* Grafana dashboards
* web dashboard integration
* Helm/GitOps integration
* configurable AI provider
* provider health checks

Representative commits include:

* `feat: implement dashboard API and update analysis repository to use domain mappers`
* `refactor: migrate dashboard logic to consolidated services and update schemas`
* `refactor: overhaul dashboard API to integrate live cluster metrics and consolidate analysis reporting`
* `14c59cc0` — health checks for Loki, OpenTelemetry and AI
* `17232797` — lazy AI provider initialisation
* `2cd389db` — AI provider configuration
* `093a43a9` — Ollama Helm configuration

The project also added KubeSage-oriented Grafana dashboards and later a web dashboard component.

> **Note:** Sprint 22 is deliberately marked as reconstructed rather than Git-authoritative. This prevents the roadmap from presenting an inferred sprint boundary as historical fact.

---

## Sprint 23 — Persist Analysis Trace ID

**Status:** Completed

The OpenTelemetry analysis trace became part of the persistent analysis model.

Capabilities:

* persist `trace_id` on analyses
* expose it through analysis summaries
* preserve traceability from history to Tempo
* validate end-to-end analysis traces

Representative commits:

* `2361cf93` — trace validation for AI analysis execution
* `0caf00af` — persist `trace_id` on analysis
* `67cecd21` — expose optional `trace_id` in analysis summaries

### Architectural outcome

```text
Incident Analysis
      │
      ├── persisted analysis
      └── trace_id
             │
             ▼
           Tempo
```

This makes every stored analysis potentially auditable at execution level.

---

## Sprint 24 — Application Error Intelligence

**Status:** In progress / evolving

Sprint 24 represents a broader move from simply detecting application errors to understanding them in incident context.

The work includes:

* application-error classification
* timeline integration
* structured error metadata
* temporal correlation
* better prompt representation
* error aggregation
* reduction of duplicate evidence
* relationship between application errors and infrastructure findings

The current implementation is evolving toward:

```text
Application logs
      ↓
Error classification
      ↓
Timeline
      ↓
Correlation with K8s + metrics
      ↓
Incident Intelligence
      ↓
AI reasoning
```

---

# 5. AI Context Optimisation

**Status:** In progress

A major current challenge is LLM hallucination and prompt growth.

The project is therefore moving away from the idea that:

> **more context is always better.**

KubeSage already collects a large amount of evidence. The next architectural problem is selecting the most valuable subset.

Recent Git history shows a deliberate optimisation layer around timeline selection:

* configurable timeline filtering
* deduplication
* priority-based limiting
* context matching
* integrity tests
* aggregation of identical timeline errors
* structured metadata in prompts
* removal of redundant normalisation logic
* deduplication of important events before aggregation

Representative commits:

* `f1fff446` — AI timeline filtering and configuration
* `8fc04bc3` — deduplication, priority-based limiting and context matching
* `7d0bd298` — timeline filtering/integrity tests
* `ce6a1443` — aggregate identical timeline error events
* `32564ee1` — structured timeline/evidence details in prompts
* `77a38256` — deduplicate important events before error aggregation

### Current architectural direction

```text
Incident Intelligence
        ↓
AI Context Selector
        ├── relevance
        ├── priority
        ├── temporal proximity
        ├── deduplication
        └── token budget
        ↓
Minimal high-value context
        ↓
LLM
```

This is strategically important:

> **KubeSage should provide the LLM with the best evidence, not the maximum amount of evidence.**

---

# 6. Current State — September 2026

KubeSage has reached a significantly different architectural maturity than the original Kubernetes diagnostic tool.

## Current pipeline

```text
                   ┌──────────────────┐
                   │    Kubernetes    │
                   └────────┬─────────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
         K8s events      Prometheus       Loki
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                    Incident Collection
                            │
                            ▼
                    Diagnostic Engine
                            │
                            ▼
                      Findings
                            │
                            ▼
                  Finding Correlation
                            │
                            ▼
                  Incident Intelligence
                     ┌──────┼──────┐
                     │      │      │
                findings  causes  timeline
                     │      │      │
                     └──────┼──────┘
                            ▼
                    AI Context Selector
                            │
                            ▼
                       Prompt Builder
                            │
                            ▼
                           LLM
                            │
                            ▼
                     Structured AI Report
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
           Quality Evaluation      Persistence
                                       │
                                       ▼
                                  History / Web UI
```

---

# 7. Observability of KubeSage

KubeSage also observes itself.

The platform has progressively added:

* structured logging
* Prometheus operational metrics
* HTTP request metrics
* analysis duration metrics
* Kubernetes operation metrics
* LLM request/token/duration metrics
* watcher metrics
* OpenTelemetry traces
* Grafana dashboards
* trace validation tests

The system therefore has two observability layers.

## Observability of the monitored cluster

```text
Kubernetes / Prometheus / Loki / Tempo
              ↓
           KubeSage
              ↓
       Incident Intelligence
```

## Observability of KubeSage itself

```text
KubeSage
   ↓
OpenTelemetry + Prometheus + structured logs
   ↓
Grafana / Tempo / Loki
```

This distinction is important when presenting the project professionally:

> KubeSage is both an **incident analysis engine** and a **production-style observable service**.

---

# 8. Product Positioning

KubeSage is not intended to replace Grafana.

The two systems solve different problems.

| Tool       | Primary role                                        |
| ---------- | --------------------------------------------------- |
| Prometheus | Metrics storage/querying                            |
| Loki       | Log storage/querying                                |
| Tempo      | Distributed tracing                                 |
| Grafana    | Observability exploration and dashboards            |
| KubeSage   | Incident investigation, correlation and explanation |

Grafana answers questions such as:

> **"What is happening in the cluster?"**

KubeSage aims to answer:

> **"What happened, why is it probably happening, what evidence supports that conclusion, and what should I investigate or do next?"**

The web UI therefore complements Grafana rather than attempting to replace it.

---

# 9. Architectural Milestones

The most important architectural transitions are:

1. **Kubernetes inspection → deterministic diagnostics**
2. **Individual rules → structured findings**
3. **Kubernetes-only evidence → multi-source observability evidence**
4. **Independent findings → correlated findings**
5. **Stateless analysis → persistent incident history**
6. **Manual analysis → proactive watcher**
7. **Point-in-time snapshot → incident timeline**
8. **Findings + timeline → incident intelligence**
9. **Generic LLM prompt → structured evidence-driven AI context**
10. **AI generation → AI quality evaluation and grounding**
11. **AI context growth → context selection and token budgeting**
12. **Analysis result → traceable, observable analysis execution**

---

# 10. Current Technical Priorities

Based on the latest implementation direction, the next priorities should focus less on adding raw data sources and more on making the existing evidence **reliable, relevant and actionable**.

## Priority 1 — AI Context Engineering

* strict token budgets
* evidence ranking
* temporal relevance
* deduplication
* source diversity without redundancy
* deterministic context selection
* explicit uncertainty
* contradiction handling
* prevention of unsupported conclusions

## Priority 2 — Application Intelligence

* richer application error classification
* stack-trace understanding
* error grouping
* request/trace correlation
* application error → infrastructure cause relationships
* service-level impact

## Priority 3 — Incident Intelligence

* stronger causal relationships
* confidence propagation
* root-cause ranking
* impact analysis
* incident lifecycle/state
* recurring incident detection

## Priority 4 — AI Evaluation

* regression datasets
* model benchmarks
* grounding metrics
* hallucination rate
* evidence attribution accuracy
* recommendation usefulness
* deterministic-vs-LLM agreement metrics

## Priority 5 — SRE Actionability

The natural long-term evolution of the current architecture is:

```text
Observe
   ↓
Explain
   ↓
Recommend
   ↓
Act
```

The **Act** stage should only be introduced after evidence grounding, confidence and safety controls are sufficiently mature.

---

# 11. Roadmap Maintenance Rules

This file is intended to become the canonical high-level history of KubeSage.

To avoid the historical ambiguity that led to its creation:

1. Keep this file in the main repository.
2. Update it when a major architectural milestone is completed.
3. Do not require sprint branches to maintain it.
4. When sprint numbering is informal, document the milestone by **name + date + status** rather than inventing a number.
5. Link important milestones to representative commits when useful.
6. Keep implementation details in code documentation; keep this file focused on architectural evolution and product direction.
7. Prefer documenting **why a capability exists** rather than merely listing files that changed.

---

# 12. Historical Confidence

## High confidence

The following milestones are directly supported by named Git commits and/or project development history:

* Kubernetes service and diagnostic rules
* Prometheus integration
* Loki integration
* Tempo/OpenTelemetry integration
* finding correlation
* PostgreSQL persistence
* Kubernetes watcher
* OpenTelemetry analysis tracing
* Incident Timeline
* Incident Intelligence
* application error detection
* AI report quality testing
* AI evidence grounding/validation
* analysis trace ID persistence
* AI timeline/context filtering
* metric change detection

## Medium confidence

The exact sprint numbering of some intermediate phases is reconstructed from the project's development chronology because Git does not encode sprint boundaries.

In particular:

> **Sprint 22 and some early sprint numbers should be treated as historical labels rather than Git-defined milestones.**

This distinction is intentional.

The goal of this document is to preserve the evolution of the architecture without creating false historical precision.

---

# 13. Current Milestone

**September 2026 — KubeSage is transitioning from an AI-assisted diagnostic engine into an evidence-driven incident intelligence platform.**

The central engineering problem is no longer simply collecting more information.

It is:

> **Selecting the smallest set of trustworthy, temporally relevant and causally meaningful evidence that allows deterministic diagnostics and an LLM to explain an incident without hallucinating.**

That principle should guide the next iterations of KubeSage.
