-- PersonaOps v1 schema (starter)

CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  flow_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  persona_id TEXT NOT NULL,
  channel TEXT NOT NULL,
  channel_message_id TEXT,
  type TEXT NOT NULL,
  revision INTEGER NOT NULL,
  trace_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  payload JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_flow_id_ts ON events(flow_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS flow_snapshots (
  flow_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  status TEXT NOT NULL,
  revision INTEGER NOT NULL,
  open_tasks JSONB NOT NULL,
  latest_decisions JSONB NOT NULL,
  owners JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS outbox (
  id BIGSERIAL PRIMARY KEY,
  idempotency_key TEXT UNIQUE NOT NULL,
  channel TEXT NOT NULL,
  target TEXT NOT NULL,
  body JSONB NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  retry_count INTEGER NOT NULL DEFAULT 0,
  next_attempt_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
