# Flowscribe – Automated C4 Architecture Analysis & Documentation

## Overview
Flowscribe automates generation, visualization, and review of multi-level C4 architecture models for large repositories.
It integrates static analysis (Deptrac), dynamic LLM review (context-aware prompts), and cost tracking (usage-first accounting)
to produce end-to-end architecture insights.

## Core Features
- Automated C4 Level 1–4 document generation
- AI-driven architecture review using premium LLMs (Sonnet 4.5, Xi Fast Code)
- Cost-aware metrics and usage validation (OpenRouter accounting)
- Provenance stamping and audit logging
- Extensible Mermaid-based visualization with Deptrac layer integration

## Architecture & Workflow
Flowscribe follows a modular pipeline:

1. **Dependency Analysis (Deptrac)** – Identifies cross-layer calls and structural violations.
2. **C4 Model Generation** – Sequential L1 → L4 markdown generation using task-specific LLM prompts.
3. **Architecture Review** – Deep architectural inspection with Sonnet 4.5, outputting recommendations.
4. **Metrics Aggregation** – Canonicalized metrics schema (v1.0) across all scripts for uniform cost tracking.
5. **Visualization Rendering** – Rich layered overview using Mermaid with true inter-layer arrows.
6. **Validation & Provenance** – Hash-stamped outputs for reproducibility and verification.

## Visualization
Flowscribe’s visualization layer uses the Deptrac ruleset to render actual dependencies between layers.

### Example: Inter-Layer Dependency Diagram (via Deptrac Ruleset)

```mermaid
flowchart TB
    subgraph Presentation["Presentation Layer"]
        Controller[Controller Layer]
    end

    subgraph Domain["Domain Layer"]
        Service[Service Layer]
    end

    subgraph Infrastructure["Infrastructure Layer"]
        Database[(Database)]
        External["External Services"]
    end

    Controller --> Service
    Service --> Database
    Service --> External
```
> **Note:** Layers with no direct dependencies are displayed in gray for completeness.

## Metrics & Costing
Flowscribe adopts a **usage-first** approach where all cost metrics are sourced directly from OpenRouter API usage data.
Each script reports metrics in a canonical schema:

| Field | Description |
|-------|--------------|
| `model` | LLM model used (e.g., claude-sonnet-4.5) |
| `tokens_in` / `tokens_out` | Prompt and completion tokens |
| `cost_usd` | Cost derived from OpenRouter accounting |
| `duration_sec` | Execution time |
| `source` | Script or level producing this metric |

### Example Cost Summary (aggregated)
| Stage | Model | Cost (USD) | Tokens (in/out) | Duration (s) |
|--------|--------|-------------:|-----------------:|-------------:|
| 🧭 C4 Level 1 | gpt-4o-mini | 0.0065 | 2,345 / 2,001 | 58.3 |
| 🏗️ C4 Level 2 | gpt-4o-mini | 0.0102 | 4,231 / 3,765 | 102.1 |
| 🧩 C4 Level 3 | gpt-4o-mini | 0.0087 | 3,221 / 2,998 | 95.4 |
| ⚙️ C4 Level 4 | claude-sonnet-4.5 | 0.0198 | 8,750 / 7,690 | 165.4 |
| 🧱 Architecture Review | claude-sonnet-4.5 | 0.0133 | 8,750 / 7,690 | 165.4 |
| 💼 **TOTAL** |  | **$0.0585** | **27,297 / 24,144** | **586.6** |

_Legend: “in” = prompt tokens, “out” = completion tokens. Costs use OpenRouter usage accounting._

## Validation & Provenance
All generated files include provenance stamps for traceability:

- **Hashing** – Each markdown is SHA256-hashed post-generation.
- **Versioning** – Scripts include `flowscribe_utils` version stamps.
- **Verification tools** –
  - `flowscribe verify-metrics` validates metrics schema conformance.
  - `flowscribe verify-costs` reconciles with OpenRouter usage data.

## Roadmap

### Phase 1 (Completed ✅)
- Canonical metrics schema (v1.0)
- Usage-first cost tracking
- Violations table (Level 2)
- Dynamic LLM-based architecture review
- Mermaid rich layered visualization

### Phase 2 (In Progress 🚧)
- Full provenance and validation chain
- Cost reconciliation from OpenRouter dashboard
- Metrics aggregator (flowscribe-analyze)
- Multi-repo and plugin support
- Rule-weighted dependency visualization

### Phase 3 (Planned 🧩)
- Multi-threaded generation
- Interactive dashboards (metrics + visualization)
- Integration with CI/CD pipelines
- Enhanced audit trail and anomaly detection

## License
© 2025 Flowscribe Project. MIT License.
