# PersonaOps v1 PRD

- Status: Draft for implementation (actionable)
- Owner: Persona Platform
- Last updated: 2026-02-28 (KST)

## 1. Problem Statement

We need a production-grade virtual persona that:

1. Feels consistent and human-like across multiple channels.
2. Can execute real work (tasks, SOPs, research, external communication).
3. Avoids exposing internal meta behavior (tools, self-editing, system details).
4. Maintains project continuity over weeks/months.
5. Operates safely under strict approval and audit controls.

Current risks:

- Channel-local memory causes contradiction and drift.
- No single source of truth (SSOT) for project state.
- High-risk actions can bypass approval.
- Long-running workflows fail or lose context after interruptions.

## 2. Goals

### Primary goals

- G1: Multi-channel consistency with a project-level SSOT.
- G2: Persona separation (Front/Ops/Worker) to prevent behavior leakage.
- G3: Policy-enforced approvals for high-risk actions.
- G4: Durable execution and replayable audit trails.

### Success metrics (Go-Live)

- M1: Cross-channel contradiction rate < 1%.
- M2: Unauthorized external sends = 0.
- M3: Duplicate outbound sends = 0.
- M4: Flow resume success after failure >= 99%.
- M5: Regression suite pass rate >= 95%.

## 3. Non-Goals (v1)

- Full autonomous legal/financial decision-making.
- End-user-visible “secretly human” deception policies.
- Full omni-channel day-1 rollout (v1 starts with 2 channels).

## 4. Users / Actors

- Front Persona: external communication only.
- Ops Persona: policy, config, release, review, escalation.
- Worker: tool execution only; no external send authority.
- Human Approver: final gate for high-risk actions.

## 5. Product Principles

1. Channel is I/O, project state is truth.
2. Every action is an event, not an implicit memory mutation.
3. High-risk actions require explicit approval.
4. Persona output must hide implementation internals.
5. Quality gates block release regressions.

## 6. Functional Requirements

- FR-01: Normalize inbound events from all channels.
- FR-02: Resolve identity across channels into `actor_id`.
- FR-03: Correlate events into `project_id` + `flow_id`.
- FR-04: Enforce state transitions via a flow state machine.
- FR-05: Use optimistic concurrency (`revision`) for updates.
- FR-06: Compile per-turn context packs from SSOT + relevant events.
- FR-07: Block meta/system leakage in Front responses.
- FR-08: Isolate Worker from external send capability.
- FR-09: Outbox idempotency for outbound sends.
- FR-10: Audit logging and event replay.
- FR-11: Approval workflow for high-risk actions.
- FR-12: Tracing and evaluation integrated into CI/CD.

## 7. Core Data Contracts

Mandatory event keys:

- `event_id`
- `project_id`
- `flow_id`
- `task_id`
- `actor_id`
- `persona_id`
- `revision`
- `trace_id`
- `timestamp`

## 8. Safety & Governance

High-risk categories (approval required):

- External legal/commercial commitments
- Financial transactions
- Account/security privilege changes
- Public announcements

Policy decisions are code-backed and auditable.

## 9. Rollout Plan

- Phase 1: Single persona, two channels, controlled pilot.
- Phase 2: Additional channels + task types.
- Phase 3: Multi-persona expansion with shared worker pool.

## 10. Open Questions

- Which channels are in pilot scope (Discord + Slack default)?
- What is final legal policy for persona disclosure language?
- Which data retention period is required by compliance?
