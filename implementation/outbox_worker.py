from __future__ import annotations

from typing import Callable

from .models import OutboxMessage
from .store import InMemoryStore
from .trace import trace_log

SenderFn = Callable[[OutboxMessage], None]


def process_outbox_once(store: InMemoryStore, sender: SenderFn, *, max_retries: int = 3) -> dict:
    processed = 0
    sent = 0
    failed = 0
    dead_letter = 0

    for msg in store.get_due_outbox(limit=100):
        processed += 1
        try:
            sender(msg)
            store.mark_outbox_sent(msg.idempotency_key)
            sent += 1
            trace_log(
                "outbox_sent",
                flow_id=msg.flow_id,
                task_id=msg.task_id,
                idempotency_key=msg.idempotency_key,
            )
        except Exception as exc:  # noqa: BLE001
            store.mark_outbox_retry(msg.idempotency_key, str(exc), max_retries=max_retries)
            latest = store.outbox[msg.idempotency_key]
            if latest.status == "dead_letter":
                dead_letter += 1
                trace_log(
                    "outbox_dead_letter",
                    flow_id=msg.flow_id,
                    task_id=msg.task_id,
                    idempotency_key=msg.idempotency_key,
                    error=str(exc),
                )
            else:
                failed += 1
                trace_log(
                    "outbox_retry_scheduled",
                    flow_id=msg.flow_id,
                    task_id=msg.task_id,
                    idempotency_key=msg.idempotency_key,
                    retry_count=latest.retry_count,
                    error=str(exc),
                )

    return {
        "processed": processed,
        "sent": sent,
        "failed": failed,
        "dead_letter": dead_letter,
    }
