from __future__ import annotations

import subprocess
from typing import Callable

import httpx

from .models import OutboxMessage
from .settings import Settings
from .trace import trace_log

SenderFn = Callable[[OutboxMessage], None]


class SenderError(RuntimeError):
    pass


def _extract_text(msg: OutboxMessage) -> str:
    body = msg.body or {}
    if isinstance(body.get("content"), str) and body["content"].strip():
        return body["content"]
    if isinstance(body.get("text"), str) and body["text"].strip():
        return body["text"]
    return f"[{msg.intent}] flow={msg.flow_id} task={msg.task_id}"


def _send_mock(msg: OutboxMessage) -> None:
    trace_log(
        "outbound_mock_sent",
        flow_id=msg.flow_id,
        task_id=msg.task_id,
        channel=msg.channel,
        target=msg.target,
        idempotency_key=msg.idempotency_key,
    )


def _send_internal_noop(msg: OutboxMessage) -> None:
    trace_log(
        "outbound_internal_noop",
        flow_id=msg.flow_id,
        task_id=msg.task_id,
        idempotency_key=msg.idempotency_key,
    )


def _send_webhook(msg: OutboxMessage, settings: Settings) -> None:
    text = _extract_text(msg)

    if msg.channel == "discord":
        if not settings.discord_webhook_url:
            raise SenderError("DISCORD webhook URL is not configured")
        payload = {"content": text}
        url = settings.discord_webhook_url
    elif msg.channel == "slack":
        if not settings.slack_webhook_url:
            raise SenderError("SLACK webhook URL is not configured")
        payload = {"text": text}
        url = settings.slack_webhook_url
    elif msg.channel == "internal":
        _send_internal_noop(msg)
        return
    else:
        raise SenderError(f"unsupported channel for webhook sender: {msg.channel}")

    with httpx.Client(timeout=10.0) as client:
        resp = client.post(url, json=payload)
        if resp.status_code >= 400:
            raise SenderError(f"webhook send failed ({resp.status_code}): {resp.text[:200]}")


def _send_openclaw_cli(msg: OutboxMessage, settings: Settings) -> None:
    if msg.channel == "internal":
        _send_internal_noop(msg)
        return

    text = _extract_text(msg)
    cmd = [
        settings.openclaw_cli_path,
        "message",
        "send",
        "--channel",
        msg.channel,
        "--target",
        msg.target,
        "--message",
        text,
        "--json",
    ]

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=settings.openclaw_cli_timeout_sec,
        check=False,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        raise SenderError(f"openclaw send failed ({proc.returncode}): {stderr[:280]}")

    trace_log(
        "outbound_openclaw_sent",
        flow_id=msg.flow_id,
        task_id=msg.task_id,
        channel=msg.channel,
        target=msg.target,
        idempotency_key=msg.idempotency_key,
    )


def build_sender(settings: Settings) -> SenderFn:
    mode = settings.outbound_mode.lower().strip()

    if mode == "mock":
        return _send_mock
    if mode == "webhook":
        return lambda msg: _send_webhook(msg, settings)
    if mode in {"openclaw", "openclaw_cli"}:
        return lambda msg: _send_openclaw_cli(msg, settings)

    raise SenderError(f"unsupported outbound mode: {settings.outbound_mode}")
