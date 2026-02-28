#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-your-org/personaops}"

create_label() {
  local name="$1"
  local color="$2"
  gh label create "$name" --color "$color" --repo "$REPO" 2>/dev/null || true
}

create_issue() {
  local title="$1"
  local labels="$2"
  local body="$3"
  gh issue create --repo "$REPO" --title "$title" --label "$labels" --body "$body"
}

create_label "type:story" "0ea5e9"
create_label "type:incident" "d93f0b"
create_label "status:triage" "fbca04"
create_label "priority:P0" "b60205"
create_label "priority:P1" "d93f0b"
create_label "epic:platform" "5319e7"
create_label "epic:policy" "5319e7"
create_label "epic:execution" "5319e7"
create_label "epic:channel" "5319e7"
create_label "epic:observability" "5319e7"

create_issue "[PER-001] Repo bootstrap + CI" "type:story,status:triage,priority:P0,epic:platform" "Set up CI checks and protected branch strategy."
create_issue "[PER-003] Flow state machine" "type:story,status:triage,priority:P0,epic:platform" "Implement allowed transitions and revision-safe updates."
create_issue "[PER-102] Approval gate" "type:story,status:triage,priority:P0,epic:policy" "High-risk actions must require explicit approval."
create_issue "[PER-202] Outbox idempotency + retry" "type:story,status:triage,priority:P0,epic:execution" "Reliable outbound queue with dead-letter fallback."
create_issue "[PER-301] Discord adapter" "type:story,status:triage,priority:P1,epic:channel" "Canonical event ingestion from Discord payloads."
create_issue "[PER-401] Trace + eval pipeline" "type:story,status:triage,priority:P1,epic:observability" "Integrate structured tracing and regression gates."

echo "Seed issues created for $REPO"
