from __future__ import annotations

from .settings import get_settings
from .store import InMemoryStore, StoreBackend
from .store_postgres import PostgresStore


def build_store() -> StoreBackend:
    settings = get_settings()
    backend = settings.store_backend.lower().strip()

    if backend == "postgres":
        if not settings.postgres_dsn:
            raise RuntimeError("PERSONAOPS_POSTGRES_DSN is required when PERSONAOPS_STORE_BACKEND=postgres")
        return PostgresStore(settings.postgres_dsn)

    return InMemoryStore()
