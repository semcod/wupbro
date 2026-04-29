"""Driver endpoints exposed by wupbro.

  - /drivers/dom-diff/capture  → uses wup.visual_diff.VisualDiffer (Playwright)
  - /drivers/browserless/screenshot → proxies a browserless container
  - /drivers/anomaly/report    → records anomaly metrics into the event store

Each driver degrades gracefully if its underlying dependency is missing.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException

from ..models import AnomalyReport, DomDiffRequest, ScreenshotRequest, Event
from ..storage import EventStore, get_default_store

router = APIRouter(prefix="/drivers", tags=["drivers"])


def _store() -> EventStore:
    return get_default_store()


# ---------------------------------------------------------------------------
# DOM diff driver — relies on the wup package being installed alongside.
# ---------------------------------------------------------------------------

@router.post("/dom-diff/capture")
async def dom_diff_capture(req: DomDiffRequest,
                           store: EventStore = Depends(_store)) -> Dict[str, Any]:
    """
    Trigger a one-shot DOM snapshot + diff against the previous snapshot.

    Requires: `pip install wup playwright` and `playwright install chromium`.
    """
    try:
        from wup.models.config import VisualDiffConfig
        from wup.visual_diff import VisualDiffer
    except ImportError as exc:
        raise HTTPException(503, detail=f"wup package not available: {exc}")

    cfg = VisualDiffConfig(
        enabled=True,
        pages=[req.url],
        pages_from_endpoints=False,
        max_depth=req.max_depth,
        delay_seconds=0,
    )
    differ = VisualDiffer(os.getcwd(), cfg)
    results = await differ.run_for_service(req.service, [])

    # forward each diff to the event store
    for r in results:
        store.add(Event(
            type="VISUAL_DIFF",
            service=req.service,
            url=r.get("url"),
            diff=r.get("diff"),
            timestamp=int(time.time()),
        ))
    return {"results": results}


# ---------------------------------------------------------------------------
# Browserless proxy — POSTs to an external browserless/chrome container.
# ---------------------------------------------------------------------------

@router.post("/browserless/screenshot")
async def browserless_screenshot(req: ScreenshotRequest) -> Dict[str, Any]:
    """
    Proxy to a `browserless/chrome` container.

    Set BROWSERLESS_URL (default http://browserless:3000) for the upstream.
    """
    upstream = os.environ.get("BROWSERLESS_URL", "http://browserless:3000")
    body = {"url": req.url, "options": {"fullPage": req.full_page}}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{upstream}/screenshot", json=body)
        if resp.status_code >= 400:
            raise HTTPException(resp.status_code, detail=resp.text)
        return {
            "upstream": upstream,
            "status": resp.status_code,
            "content_type": resp.headers.get("content-type", ""),
            "size_bytes": len(resp.content),
        }
    except httpx.HTTPError as exc:
        raise HTTPException(503, detail=f"browserless unreachable: {exc}")


# ---------------------------------------------------------------------------
# Anomaly driver — record numeric anomalies as events.
# ---------------------------------------------------------------------------

@router.post("/anomaly/report", status_code=201)
async def anomaly_report(report: AnomalyReport,
                         store: EventStore = Depends(_store)) -> Dict[str, Any]:
    store.add(Event(
        type="ANOMALY",
        service=report.service,
        status="anomaly",
        reason=f"{report.metric}={report.value} > threshold={report.threshold}",
        timestamp=report.timestamp,
    ))
    return {"accepted": True, "service": report.service}


@router.get("/health")
async def driver_health() -> Dict[str, Any]:
    """Best-effort capability discovery."""
    caps: Dict[str, bool] = {"events": True, "anomaly": True}
    try:
        import wup.visual_diff  # noqa: F401
        caps["dom_diff"] = True
    except ImportError:
        caps["dom_diff"] = False
    try:
        import playwright  # noqa: F401
        caps["playwright"] = True
    except ImportError:
        caps["playwright"] = False
    caps["browserless_url"] = os.environ.get("BROWSERLESS_URL", "")
    return caps
