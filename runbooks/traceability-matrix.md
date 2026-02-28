# PRD -> SDD -> Implementation Traceability

| Requirement | Design Component | Implementation Artifact |
|---|---|---|
| FR-01 Event normalization | Channel Adapter + Canonical Event | `schemas/event.schema.json`, `/events` endpoint |
| FR-04 State transition guard | Flow State Machine | `flows/default_flow.yaml`, `implementation/state_machine.py` |
| FR-05 Revision concurrency | Optimistic lock | `implementation/store.py` |
| FR-06 Context packs | Context Compiler | `implementation/context_compiler.py` |
| FR-09 Outbound idempotency | Outbox design | `implementation/store.py`, `/outbox/enqueue` |
| FR-11 Approval gating | Policy engine + approval decision | `policies/approval_rules.yaml`, `implementation/policy.py` |
| FR-12 Observability/eval | Trace + regression | `runbooks/sprint-01-02-backlog.md`, `evals/promptfooconfig.yaml` |
