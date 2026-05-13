"""Tests for /events router and EventStore."""

from __future__ import annotations


def test_post_event_accepted(client):
    resp = client.post(
        "/events",
        json={
            "type": "REGRESSION",
            "service": "users",
            "file": "app/users/routes.py",
            "endpoint": "/api/users",
            "status": "fail",
            "reason": "boom",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["accepted"] is True
    assert body["type"] == "REGRESSION"


def test_post_event_invalid_type_rejected(client):
    resp = client.post("/events", json={"type": "NOT_A_TYPE"})
    assert resp.status_code == 422


def test_list_events_returns_recent(client):
    for i in range(3):
        client.post("/events", json={"type": "PASS", "service": f"svc-{i}"})
    resp = client.get("/events")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    services = [e["service"] for e in body["items"]]
    # newest first
    assert services == ["svc-2", "svc-1", "svc-0"]


def test_list_events_filter_by_type(client):
    client.post("/events", json={"type": "REGRESSION", "service": "a"})
    client.post("/events", json={"type": "PASS", "service": "b"})
    client.post("/events", json={"type": "REGRESSION", "service": "c"})

    resp = client.get("/events?type=REGRESSION")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert all(e["type"] == "REGRESSION" for e in body["items"])


def test_list_events_filter_by_service(client):
    client.post("/events", json={"type": "PASS", "service": "users"})
    client.post("/events", json={"type": "PASS", "service": "billing"})
    resp = client.get("/events?service=users")
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["service"] == "users"


def test_list_events_limit(client):
    for i in range(20):
        client.post("/events", json={"type": "PASS", "service": f"s{i}"})
    resp = client.get("/events?limit=5")
    body = resp.json()
    assert body["total"] == 5


def test_event_stats(client):
    client.post("/events", json={"type": "REGRESSION", "service": "x"})
    client.post("/events", json={"type": "PASS", "service": "x"})
    client.post("/events", json={"type": "PASS", "service": "y"})
    resp = client.get("/events/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total"] == 3
    assert stats["by_type"]["REGRESSION"] == 1
    assert stats["by_type"]["PASS"] == 2


def test_clear_events(client):
    client.post("/events", json={"type": "PASS", "service": "x"})
    resp = client.delete("/events")
    assert resp.status_code == 204
    body = client.get("/events").json()
    assert body["total"] == 0


def test_event_extra_fields_preserved(client):
    client.post(
        "/events",
        json={
            "type": "VISUAL_DIFF",
            "service": "users",
            "url": "http://localhost/users",
            "diff": {"status": "changed", "counts": {"added": 5}},
        },
    )
    body = client.get("/events").json()
    assert body["items"][0]["diff"]["counts"]["added"] == 5
