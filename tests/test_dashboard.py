"""Tests for the dashboard HTML and meta endpoints."""

from __future__ import annotations


def test_root_serves_dashboard(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    assert "WUP Dashboard" in resp.text


def test_dashboard_alias(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert "WUP Dashboard" in resp.text


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert "version" in body


def test_openapi_schema_includes_routes(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    paths = spec["paths"]
    assert "/events" in paths
    assert "/events/stats" in paths
    assert "/drivers/anomaly/report" in paths
    assert "/drivers/health" in paths
