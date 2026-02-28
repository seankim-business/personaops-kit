from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("personaops")


@lru_cache(maxsize=1)
def _langfuse_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


@lru_cache(maxsize=1)
def _langfuse_client() -> Any | None:
    if not _langfuse_enabled():
        return None

    try:
        from langfuse import Langfuse  # type: ignore

        return Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
    except Exception:
        # fail open: tracing should never break production flow
        return None


def trace_log(action: str, **fields) -> None:
    payload = {"action": action, **fields}
    logger.info(json.dumps(payload, ensure_ascii=False))

    client = _langfuse_client()
    if client is None:
        return

    try:
        trace_id = str(fields.get("trace_id", "")) or None
        client.trace(name=action, trace_id=trace_id, metadata=fields)
    except Exception:
        # fail open to protect runtime stability
        return
