from __future__ import annotations

"""
PostgreSQL repository interfaces for PersonaOps.

Intentionally minimal in v0.1:
- gives concrete persistence contract from SDD
- keeps control_plane.py in-memory for quick iteration

Next step (v0.2): wire these repositories into control_plane via feature flag.
"""

from dataclasses import dataclass


@dataclass
class PostgresConfig:
    dsn: str


class PostgresEventRepository:
    def __init__(self, config: PostgresConfig) -> None:
        self.config = config

    def append_event(self, event: dict) -> None:
        # TODO(v0.2): implement psycopg insert into events table
        raise NotImplementedError


class PostgresFlowRepository:
    def __init__(self, config: PostgresConfig) -> None:
        self.config = config

    def get_flow(self, flow_id: str) -> dict | None:
        # TODO(v0.2): implement select flow snapshot
        raise NotImplementedError

    def upsert_flow_with_revision(self, flow: dict, expected_revision: int) -> dict:
        # TODO(v0.2): implement optimistic-lock upsert
        raise NotImplementedError


class PostgresOutboxRepository:
    def __init__(self, config: PostgresConfig) -> None:
        self.config = config

    def enqueue(self, message: dict) -> bool:
        # TODO(v0.2): implement idempotent outbox insert
        raise NotImplementedError
