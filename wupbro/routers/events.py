"""POST /events — receive events from WUP agents.

GET /events — list recent events (filterable by type/service).
GET /events/stats — aggregate counts by type.
DELETE /events — clear the store (admin/debug).

Events trigger notifications for subscribed clients.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Query, Depends

from ..models import Event, EventList
from ..notifications import get_notification_manager
from ..storage import EventStore, get_default_store

router = APIRouter(prefix="/events", tags=["events"])


def _store() -> EventStore:
    return get_default_store()


@router.post("", status_code=201)
async def post_event(event: Event, store: EventStore = Depends(_store)) -> dict:
    store.add(event)
    
    # Process notifications for this event
    notification_manager = get_notification_manager(store)
    notifications = notification_manager.process_event(event)
    
    # Push notifications to SSE clients
    for sub_id, payload in notifications:
        notification_manager.push_to_sse(payload)
    
    return {
        "accepted": True, 
        "type": event.type, 
        "timestamp": event.timestamp,
        "notifications_sent": len(notifications)
    }


@router.get("", response_model=EventList)
async def list_events(
    type: Optional[str] = Query(None, description="Filter by event type"),
    service: Optional[str] = Query(None, description="Filter by service name"),
    limit: int = Query(100, ge=1, le=1000),
    store: EventStore = Depends(_store),
) -> EventList:
    items = store.list(type_filter=type, service_filter=service, limit=limit)
    return EventList(items=items, total=len(items))


@router.get("/stats")
async def event_stats(store: EventStore = Depends(_store)) -> dict:
    return store.stats()


@router.delete("", status_code=204)
async def clear_events(store: EventStore = Depends(_store)) -> None:
    store.clear()
