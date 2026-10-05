# APIC -> Kong Modernization
## Codex Operating Instructions

### Project Objective

Build an evidence-driven discovery and modernization engine for the
IBM API Connect estate before migration to Kong.

The project must not perform a blind APIC-to-Kong object conversion.

Primary operating model:

Codex discovers
-> Integration Architect validates
-> Enterprise Architect decides.

---

## Source Evidence

The `staging/` directory contains raw APIC export artifacts.

Treat all files under `staging/` as immutable evidence.

DO NOT:
- modify files under staging/
- normalize files in place
- rename source evidence
- delete source evidence
- write secrets into generated outputs

Derived artifacts must be written only to:
- indexes/
- outputs/

---

## Core Evidence Rules

1. Never invent relationships.
2. Never invent backend endpoints.
3. Never infer runtime usage from configuration.
4. Never automatically declare an API retired.
5. Never classify APIs as duplicates from names alone.
6. Preserve provenance for important derived findings.
7. URI/object identifiers are primary relationship keys where available.
8. Object names are fallback evidence only.
9. Missing evidence must remain explicit.
10. Deterministic analysis must precede semantic/LLM reasoning.
11. Domain and exposure channel are separate concepts.
12. APIC Product is an AS-IS object and must not automatically become a Kong Product.
13. Sensitive credential values must never appear in generated reports or indexes.

---

## Initial Pipeline

Raw Evidence
-> Repository Profiling
-> Object Extraction
-> Canonical Indexing
-> URI Resolution
-> Relationship Reconstruction
-> API Structural Inventory
-> Backend Resolution
-> Semantic Enrichment
-> Runtime Enrichment
-> Rationalization

Do not implement later phases unless explicitly requested.

---

## Phase 1 Scope

Current work is limited to:

- repository profiling
- file discovery
- YAML/JSON parsing
- file hashing
- schema-family detection
- exact duplicate detection
- parse error reporting

No semantic API classification is allowed in this phase.

---

## Testing

Run:

pytest

Before completing a task:
- run relevant unit tests
- run smoke tests if applicable
- report failures explicitly
- do not hide unresolved errors