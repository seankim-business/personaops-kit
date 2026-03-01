# PersonaOps v1 SDD (System Design Document)

- Status: Implementation baseline
- Related: `PRD.md`

## 1. Architecture Overview

Three-plane architecture:

1. **Persona Plane (Front)**
   - Channel-facing responses
   - No direct tool or policy mutation
2. **Control Plane (Ops + Orchestrator)**
   - Event ingestion, correlation, state transitions
   - Policy checks, approval routing
3. **Execution Plane (Worker Pool)**
   - Tool invocation, SOP execution
   - No outbound channel permission

## 2. Components

- Channel Adapter
  - Converts provider payloads to canonical events.
- Event Store (append-only)
  - Source of truth for all transitions and actions.
- Flow Store (snapshot)
  - Latest materialized state by flow.
- Correlator
  - Determines `project_id`, `flow_id`, `task_id`.
- Orchestrator
  - Applies state machine transitions.
- Policy Engine
  - Evaluates action permissions + approval requirements.
- Approval Service
  - Tracks pending/approved/rejected requests.
- Worker Dispatcher
  - Schedules and tracks execution jobs.
- Outbox
  - Reliable outbound send queue + idempotency.
- Outbound Sender
  - Mode-driven sender (`mock` / `webhook`) for channel delivery.
- Store Factory
  - Selects memory/postgres backend at runtime via environment.
- Context Compiler
  - Builds minimal per-turn context pack.
- Observability
  - Trace spans, metrics, structured logs.

## 3. Data Model

### 3.1 Canonical Event

See `schemas/event.schema.json`.

### 3.2 Flow State Snapshot

See `schemas/flow_state.schema.json`.

## 4. State Machine

Default flow states:

- `new`
- `triage`
- `executing`
- `waiting_approval`
- `ready_to_send`
- `sent`
- `done`
- `blocked`

Allowed transitions are defined in `flows/default_flow.yaml`.

## 5. Concurrency Strategy

- Flow updates must provide expected `revision`.
- If mismatch: reject + retry with refreshed snapshot.
- Writes are append-first (event), then snapshot update.

## 6. Approval Strategy

- Policy returns one of:
  - `allow`
  - `deny`
  - `requires_approval`
- `requires_approval` emits approval request event and transitions to `waiting_approval`.

## 7. Outbound Reliability

- All outbound actions write to Outbox.
- Idempotency key format:
  - `{channel}:{target}:{flow_id}:{task_id}:{intent_hash}`
- Sender retries with backoff; duplicate keys are ignored.
- Sender mode (`PERSONAOPS_OUTBOUND_MODE`):
  - `mock` (default): trace-only send for safe test/dev environments.
  - `webhook`: real sends via channel webhooks (Discord/Slack).
- Webhook mode requires channel-specific URLs:
  - `PERSONAOPS_DISCORD_WEBHOOK_URL`
  - `PERSONAOPS_SLACK_WEBHOOK_URL`

## 8. Context Compilation

Inputs:
- Persona static profile
- Current flow snapshot
- Recent decision events
- Open tasks/blockers

Output:
- Bounded context object with token budget guards.

## 9. Security Model

- RBAC by role (`front`, `ops`, `worker`, `approver`).
- Worker has no `send_external` capability.
- Secret material scoped per task (short-lived where possible).
- Audit every policy decision and approval action.

## 10. Observability

- Required IDs in all logs: `trace_id`, `event_id`, `flow_id`, `revision`.
- Trace spans:
  - `ingest_event`
  - `correlate_flow`
  - `policy_evaluate`
  - `dispatch_worker`
  - `outbox_send`
- Langfuse integration mode:
  - Enabled when `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` are present.
  - Fail-open behavior (trace errors must not break request handling).

## 11. Testing Strategy

- Unit:
  - state transition validity
  - policy decision logic
  - idempotency behavior
- Integration:
  - channel -> event -> flow transition
  - approval round-trip
- Regression:
  - prompt/eval suite in `evals/`

## 12. Deployment (v1)

- Control plane: Python FastAPI service.
- Backend selection via env:
  - `PERSONAOPS_STORE_BACKEND=memory|postgres`
  - `PERSONAOPS_POSTGRES_DSN=...` (required when postgres)
- Stores: memory backend for local dev; PostgresStore + repositories for production persistence.
- Worker: outbox worker for reliable outbound processing (retry + dead-letter).
- Channel adapters: Discord adapter included in v0.3 baseline.
- Temporal: orchestration scaffold included (`implementation/temporal_workflow.py`), full worker registration pending next integration loop.

## 13. Failure Handling

- Worker failure: retry policy + dead-letter.
- Snapshot conflict: optimistic lock retry.
- Outbound failure: backoff and retry until threshold.
- Global incident: switch to `safe_mode` (read + draft only).

## 14. Distribution & Injection

- Project is package-enabled via `pyproject.toml`.
- Distribution artifact: `personaops-kit` wheel/sdist.
- CLI entrypoint: `personaops-kit`.
  - `personaops-kit init <target>`: scaffold a standalone PersonaOps project.
  - `personaops-kit inject <workspace> --profile openclaw|nanobot --name personaops`: inject starter into existing workspace.
- Packaged template payload lives under `src/personaops_kit/templates/personaops-starter`.
