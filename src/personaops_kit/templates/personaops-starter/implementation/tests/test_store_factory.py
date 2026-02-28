import os

import pytest

from implementation.store import InMemoryStore
from implementation.store_factory import build_store


@pytest.mark.parametrize("backend", [None, "memory", " MEMORY "])
def test_build_store_defaults_to_memory(backend, monkeypatch):
    if backend is None:
        monkeypatch.delenv("PERSONAOPS_STORE_BACKEND", raising=False)
    else:
        monkeypatch.setenv("PERSONAOPS_STORE_BACKEND", backend)
    monkeypatch.delenv("PERSONAOPS_POSTGRES_DSN", raising=False)

    store = build_store()
    assert isinstance(store, InMemoryStore)


def test_build_store_postgres_requires_dsn(monkeypatch):
    monkeypatch.setenv("PERSONAOPS_STORE_BACKEND", "postgres")
    monkeypatch.delenv("PERSONAOPS_POSTGRES_DSN", raising=False)

    with pytest.raises(RuntimeError):
        build_store()

    monkeypatch.delenv("PERSONAOPS_STORE_BACKEND", raising=False)
