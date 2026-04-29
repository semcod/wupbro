"""Shared fixtures for wupbro tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from wupbro.main import create_app
from wupbro.storage import EventStore, set_default_store


@pytest.fixture
def fresh_store():
    store = EventStore(jsonl_path=None, capacity=100)
    set_default_store(store)
    yield store
    set_default_store(EventStore(jsonl_path=None))


@pytest.fixture
def client(fresh_store) -> TestClient:
    app = create_app()
    return TestClient(app)
