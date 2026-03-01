import subprocess

import pytest

from implementation.models import OutboxMessage
from implementation.sender import SenderError, build_sender
from implementation.settings import Settings


def _msg(channel: str = "discord") -> OutboxMessage:
    return OutboxMessage(
        idempotency_key="k1",
        channel=channel,
        target="ch",
        flow_id="flow_1",
        task_id="task_1",
        intent="notify",
        body={"text": "hello"},
    )


def test_mock_sender_no_error():
    sender = build_sender(Settings(outbound_mode="mock"))
    sender(_msg())


def test_webhook_sender_requires_url():
    sender = build_sender(Settings(outbound_mode="webhook", discord_webhook_url=""))
    with pytest.raises(SenderError):
        sender(_msg("discord"))


def test_openclaw_sender_invokes_cli(monkeypatch):
    called = {}

    def fake_run(cmd, capture_output, text, timeout, check):  # noqa: ANN001
        called["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout='{"ok":true}', stderr="")

    monkeypatch.setattr("implementation.sender.subprocess.run", fake_run)

    sender = build_sender(Settings(outbound_mode="openclaw", openclaw_cli_path="openclaw"))
    sender(_msg("discord"))

    assert called["cmd"][0] == "openclaw"
    assert "message" in called["cmd"]
    assert "send" in called["cmd"]
    assert "--channel" in called["cmd"]


def test_openclaw_sender_raises_on_failure(monkeypatch):
    def fake_run(cmd, capture_output, text, timeout, check):  # noqa: ANN001
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="boom")

    monkeypatch.setattr("implementation.sender.subprocess.run", fake_run)

    sender = build_sender(Settings(outbound_mode="openclaw", openclaw_cli_path="openclaw"))
    with pytest.raises(SenderError):
        sender(_msg("discord"))


def test_invalid_sender_mode_raises():
    with pytest.raises(SenderError):
        build_sender(Settings(outbound_mode="invalid"))
