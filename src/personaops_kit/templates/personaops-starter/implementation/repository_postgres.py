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


class PostgresFlowRepository:
    def __init__(self, config: PostgresConfig) -> None:
        self.config = config

    def get_flow(self, flow_id: str) -> dict[str, Any] | None:
        with psycopg.connect(self.config.dsn, row_factory=dict_row) as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM flow_snapshots WHERE flow_id = %s", (flow_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def upsert_flow_with_revision(self, flow: dict[str, Any], expected_revision: int) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        with psycopg.connect(self.config.dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # optimistic update path
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

                # insert path for brand-new flow (only when expected revision is zero)
                if expected_revision == 0:
                    cur.execute(
                        """
                        INSERT INTO flow_snapshots (
                          flow_id, project_id, status, revision, open_tasks, latest_decisions, owners, updated_at
                        ) VALUES (
                          %(flow_id)s, %(project_id)s, %(status)s, 1, %(open_tasks)s, %(latest_decisions)s, %(owners)s, %(updated_at)s
                        )
                        ON CONFLICT (flow_id) DO NOTHING
                        RETURNING *
                        """,
                        {
                            "flow_id": flow["flow_id"],
                            "project_id": flow["project_id"],
                            "status": flow["status"],
                            "open_tasks": Jsonb(flow.get("open_tasks", [])),
                            "latest_decisions": Jsonb(flow.get("latest_decisions", [])),
                            "owners": Jsonb(flow.get("owners", [])),
                            "updated_at": now,
                        },
                    )
                    inserted = cur.fetchone()
                    if inserted:
                        conn.commit()
                        return dict(inserted)

                conn.rollback()
                raise RuntimeError("revision conflict or flow not found")


class PostgresOutboxRepository:
    def __init__(self, config: PostgresConfig) -> None:
        self.config = config

    def enqueue(self, message: dict[str, Any]) -> bool:
        with psycopg.connect(self.config.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO outbox (idempotency_key, channel, target, body, status)
                VALUES (%s, %s, %s, %s, 'pending')
                ON CONFLICT (idempotency_key) DO NOTHING
                """,
                (
                    message["idempotency_key"],
                    message["channel"],
                    message["target"],
                    Jsonb(message.get("body", {})),
                ),
            )
            return cur.rowcount > 0
