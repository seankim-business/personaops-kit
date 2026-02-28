from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


@dataclass
class PostgresConfig:
    dsn: str


class PostgresEventRepository:
    def __init__(self, config: PostgresConfig) -> None:
        self.config = config

    def append_event(self, event: dict[str, Any]) -> None:
        with psycopg.connect(self.config.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO events (
                  event_id, project_id, flow_id, task_id, actor_id, persona_id,
                  channel, channel_message_id, type, revision, trace_id, timestamp, payload
                ) VALUES (
                  %(event_id)s, %(project_id)s, %(flow_id)s, %(task_id)s, %(actor_id)s, %(persona_id)s,
                  %(channel)s, %(channel_message_id)s, %(type)s, %(revision)s, %(trace_id)s, %(timestamp)s, %(payload)s
                )
                ON CONFLICT (event_id) DO NOTHING
                """,
                {
                    **event,
                    "payload": Jsonb(event.get("payload", {})),
                },
            )

    def list_by_flow(self, flow_id: str, limit: int = 20) -> list[dict[str, Any]]:
        with psycopg.connect(self.config.dsn, row_factory=dict_row) as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM events
                WHERE flow_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (flow_id, limit),
            )
            rows = cur.fetchall()
            rows.reverse()  # oldest -> newest
            return [dict(r) for r in rows]


class PostgresFlowRepository:
    def __init__(self, config: PostgresConfig) -> None:
        self.config = config

    def ensure_flow(self, flow_id: str, project_id: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        with psycopg.connect(self.config.dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO flow_snapshots (
                      flow_id, project_id, status, revision, open_tasks, latest_decisions, owners, updated_at
                    ) VALUES (
                      %(flow_id)s, %(project_id)s, 'new', 0, '[]'::jsonb, '[]'::jsonb, '[]'::jsonb, %(updated_at)s
                    )
                    ON CONFLICT (flow_id) DO NOTHING
                    """,
                    {"flow_id": flow_id, "project_id": project_id, "updated_at": now},
                )
                cur.execute("SELECT * FROM flow_snapshots WHERE flow_id = %s", (flow_id,))
                row = cur.fetchone()
                if not row:
                    raise RuntimeError(f"failed to ensure flow: {flow_id}")
                conn.commit()
                return dict(row)

    def get_flow(self, flow_id: str) -> dict[str, Any] | None:
        with psycopg.connect(self.config.dsn, row_factory=dict_row) as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM flow_snapshots WHERE flow_id = %s", (flow_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def upsert_flow_with_revision(self, flow: dict[str, Any], expected_revision: int) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        with psycopg.connect(self.config.dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE flow_snapshots
                    SET status = %(status)s,
                        revision = %(new_revision)s,
                        open_tasks = %(open_tasks)s,
                        latest_decisions = %(latest_decisions)s,
                        owners = %(owners)s,
                        updated_at = %(updated_at)s
                    WHERE flow_id = %(flow_id)s AND revision = %(expected_revision)s
                    RETURNING *
                    """,
                    {
                        "flow_id": flow["flow_id"],
                        "status": flow["status"],
                        "new_revision": expected_revision + 1,
                        "open_tasks": Jsonb(flow.get("open_tasks", [])),
                        "latest_decisions": Jsonb(flow.get("latest_decisions", [])),
                        "owners": Jsonb(flow.get("owners", [])),
                        "updated_at": now,
                        "expected_revision": expected_revision,
                    },
                )
                row = cur.fetchone()
                if row:
                    conn.commit()
                    return dict(row)

                conn.rollback()
                raise RuntimeError("revision conflict or flow not found")


class PostgresApprovalRepository:
    def __init__(self, config: PostgresConfig) -> None:
        self.config = config

    def request(self, approval: dict[str, Any]) -> dict[str, Any]:
        with psycopg.connect(self.config.dsn, row_factory=dict_row) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO approvals (
                  approval_id, project_id, flow_id, task_id, status,
                  requested_by, requested_at, reason
                ) VALUES (
                  %(approval_id)s, %(project_id)s, %(flow_id)s, %(task_id)s, 'pending',
                  %(requested_by)s, %(requested_at)s, %(reason)s
                )
                RETURNING *
                """,
                approval,
            )
            row = cur.fetchone()
            conn.commit()
            return dict(row)

    def get(self, approval_id: str) -> dict[str, Any] | None:
        with psycopg.connect(self.config.dsn, row_factory=dict_row) as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM approvals WHERE approval_id = %s", (approval_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def list_all(self) -> list[dict[str, Any]]:
        with psycopg.connect(self.config.dsn, row_factory=dict_row) as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM approvals ORDER BY requested_at DESC")
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def decide(self, approval_id: str, *, approved_by: str, approved: bool, note: str | None) -> dict[str, Any] | None:
        status = "approved" if approved else "rejected"
        decided_at = datetime.now(timezone.utc)
        with psycopg.connect(self.config.dsn, row_factory=dict_row) as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE approvals
                SET status = %s,
                    decided_by = %s,
                    decided_at = %s,
                    note = %s
                WHERE approval_id = %s
                RETURNING *
                """,
                (status, approved_by, decided_at, note, approval_id),
            )
            row = cur.fetchone()
            conn.commit()
            return dict(row) if row else None


class PostgresOutboxRepository:
    def __init__(self, config: PostgresConfig) -> None:
        self.config = config

    def enqueue(self, message: dict[str, Any]) -> bool:
        with psycopg.connect(self.config.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO outbox (
                  idempotency_key, channel, target, flow_id, task_id, intent, body,
                  status, retry_count, next_attempt_at
                ) VALUES (
                  %(idempotency_key)s, %(channel)s, %(target)s, %(flow_id)s, %(task_id)s, %(intent)s, %(body)s,
                  %(status)s, %(retry_count)s, %(next_attempt_at)s
                )
                ON CONFLICT (idempotency_key) DO NOTHING
                """,
                {
                    **message,
                    "body": Jsonb(message.get("body", {})),
                },
            )
            return cur.rowcount > 0

    def list_all(self) -> list[dict[str, Any]]:
        with psycopg.connect(self.config.dsn, row_factory=dict_row) as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM outbox ORDER BY created_at DESC")
            return [dict(r) for r in cur.fetchall()]

    def get(self, key: str) -> dict[str, Any] | None:
        with psycopg.connect(self.config.dsn, row_factory=dict_row) as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM outbox WHERE idempotency_key = %s", (key,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_due(self, limit: int = 50) -> list[dict[str, Any]]:
        with psycopg.connect(self.config.dsn, row_factory=dict_row) as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM outbox
                WHERE status IN ('pending', 'failed')
                  AND (next_attempt_at IS NULL OR next_attempt_at <= NOW())
                ORDER BY COALESCE(next_attempt_at, created_at) ASC
                LIMIT %s
                """,
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]

    def mark_sent(self, key: str) -> None:
        with psycopg.connect(self.config.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE outbox
                SET status = 'sent', last_error = NULL, updated_at = NOW()
                WHERE idempotency_key = %s
                """,
                (key,),
            )
            conn.commit()

    def mark_retry(self, key: str, error: str, *, max_retries: int = 3) -> None:
        with psycopg.connect(self.config.dsn, row_factory=dict_row) as conn, conn.cursor() as cur:
            cur.execute("SELECT retry_count FROM outbox WHERE idempotency_key = %s", (key,))
            row = cur.fetchone()
            if not row:
                return
            retry_count = int(row["retry_count"]) + 1
            if retry_count > max_retries:
                cur.execute(
                    """
                    UPDATE outbox
                    SET status = 'dead_letter', retry_count = %s, last_error = %s, updated_at = NOW()
                    WHERE idempotency_key = %s
                    """,
                    (retry_count, error, key),
                )
            else:
                cur.execute(
                    """
                    UPDATE outbox
                    SET status = 'failed',
                        retry_count = %s,
                        last_error = %s,
                        next_attempt_at = NOW() + (%s * INTERVAL '10 seconds'),
                        updated_at = NOW()
                    WHERE idempotency_key = %s
                    """,
                    (retry_count, error, retry_count, key),
                )
            conn.commit()
