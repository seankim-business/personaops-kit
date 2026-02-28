from __future__ import annotations

import json
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("personaops")


def trace_log(action: str, **fields) -> None:
    payload = {"action": action, **fields}
    logger.info(json.dumps(payload, ensure_ascii=False))
