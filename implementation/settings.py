from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    store_backend: str = os.getenv("PERSONAOPS_STORE_BACKEND", "memory")
    postgres_dsn: str = os.getenv("PERSONAOPS_POSTGRES_DSN", "")


def get_settings() -> Settings:
    return Settings()
