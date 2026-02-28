# Sprint 01~02 Backlog (14 days)

## Goals
- Build canonical event pipeline and flow machine
- Enforce RBAC + approval gate
- Add observability and regression gate

## Priority P0
- PER-001: Repo + CI bootstrap
- PER-002: Event schema v1 validation
- PER-003: Flow state machine v1
- PER-004: Revision lock handling
- PER-101: Front/Ops/Worker RBAC
- PER-102: Outbound approval gate
- PER-202: Inbox/Outbox idempotency
- PER-301: Discord adapter
- PER-402: Prompt regression gate
- PER-502: UAT scenarios

## Priority P1
- PER-201: Temporal integration
- PER-302: Slack adapter
- PER-303: Actor identity resolution
- PER-401: Tracing pipeline
- PER-501: Canary + rollback runbook

## Exit Criteria
- Unauthorized external send = 0
- Duplicate outbound send = 0
- Contradiction rate < 1%
- Resume success >= 99%
