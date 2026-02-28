from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    store_backend: str = field(default_factory=lambda: os.getenv("PERSONAOPS_STORE_BACKEND", "memory"))
    postgres_dsn: str = field(default_factory=lambda: os.getenv("PERSONAOPS_POSTGRES_DSN", ""))
    outbox_max_retries: int = field(
        default_factory=lambda: int(os.getenv("PERSONAOPS_OUTBOX_MAX_RETRIES", "3"))
    )


def get_settings() -> Settings:
    return Settings()
