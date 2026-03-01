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


def test_invalid_sender_mode_raises():
    with pytest.raises(SenderError):
        build_sender(Settings(outbound_mode="invalid"))
