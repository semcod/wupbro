"""Tests for /drivers/* router."""

from __future__ import annotations


def test_anomaly_report_creates_event(client):
    resp = client.post("/drivers/anomaly/report", json={
        "service": "billing",
        "metric": "p95_latency",
        "value": 1500.0,
        "threshold": 1000.0,
    })
    assert resp.status_code == 201
    assert resp.json()["accepted"] is True

    events = client.get("/events").json()
    assert events["total"] == 1
    e = events["items"][0]
    assert e["type"] == "ANOMALY"
    assert e["service"] == "billing"
    assert "p95_latency" in e["reason"]


def test_driver_health_reports_capabilities(client):
    resp = client.get("/drivers/health")
    assert resp.status_code == 200
    caps = resp.json()
    assert caps["events"] is True
    assert caps["anomaly"] is True
    assert "dom_diff" in caps          # bool depending on wup install
    assert "playwright" in caps        # bool depending on playwright install


def test_browserless_unreachable_returns_503(client, monkeypatch):
    monkeypatch.setenv("BROWSERLESS_URL", "http://127.0.0.1:1")  # closed port
    resp = client.post("/drivers/browserless/screenshot", json={"url": "http://example.com"})
    assert resp.status_code == 503


def test_dom_diff_endpoint_exists(client):
    """Endpoint accepts request payload (actual diff requires Playwright)."""
    # Using a non-routable URL — VisualDiffer logs a warning and returns
    # a result with status='error' but does NOT raise.
    resp = client.post("/drivers/dom-diff/capture", json={
        "url": "http://127.0.0.1:1/",
        "service": "demo",
        "max_depth": 3,
    })
    # Either 200 (gracefully degraded) or 503 (wup not installed). Both acceptable.
    assert resp.status_code in (200, 503)
