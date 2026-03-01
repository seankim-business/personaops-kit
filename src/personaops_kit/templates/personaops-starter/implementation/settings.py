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

    # Outbound sender settings
    outbound_mode: str = field(default_factory=lambda: os.getenv("PERSONAOPS_OUTBOUND_MODE", "mock"))
    discord_webhook_url: str = field(default_factory=lambda: os.getenv("PERSONAOPS_DISCORD_WEBHOOK_URL", ""))
    slack_webhook_url: str = field(default_factory=lambda: os.getenv("PERSONAOPS_SLACK_WEBHOOK_URL", ""))



def get_settings() -> Settings:
    return Settings()
