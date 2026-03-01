# PRD -> SDD -> Implementation Traceability

| Requirement | Design Component | Implementation Artifact |
|---|---|---|
| FR-01 Event normalization | Channel Adapter + Canonical Event | `schemas/event.schema.json`, `/events`, `/adapters/discord/inbound`, `implementation/discord_adapter.py` |
| FR-04 State transition guard | Flow State Machine | `flows/default_flow.yaml`, `implementation/state_machine.py`, `/flows/{flow_id}/transition` |
| FR-05 Revision concurrency | Optimistic lock | `implementation/store.py` |
| FR-06 Context packs | Context Compiler | `implementation/context_compiler.py`, `/context/{flow_id}` |
| FR-09 Outbound idempotency | Outbox design + sender mode | `implementation/store.py`, `/outbox/enqueue`, `/outbox/process_once`, `implementation/outbox_worker.py`, `implementation/sender.py` |
| FR-10 Audit/replay foundation | Event append log | `implementation/store.py`, `/events` |
| FR-11 Approval gating | Policy engine + approval workflow | `policies/approval_rules.yaml`, `implementation/policy.py`, `/approvals/request`, `/approvals/{approval_id}/decision` |
| FR-12 Observability/eval | Trace + regression | `implementation/trace.py`, `implementation/tests/test_observability.py`, `runbooks/sprint-01-02-backlog.md`, `evals/promptfooconfig.yaml` |
| FR-13 Persistence path | Postgres repositories + SQL schema | `implementation/repository_postgres.py`, `implementation/sql/001_init.sql`, `implementation/store_postgres.py` |
| FR-14 Backend portability | Runtime-selectable backend factory | `implementation/store_factory.py`, `implementation/settings.py` |
| NFR-01 Portability/injection | Package + template installer CLI | `pyproject.toml`, `src/personaops_kit/cli.py`, `src/personaops_kit/scaffold.py` |
| NFR-02 Long-run orchestration readiness | Temporal-safe scaffold + bootstrap endpoint | `implementation/temporal_workflow.py`, `implementation/temporal_worker.py`, `/temporal/bootstrap` |
