"""Notification API router for browser notifications.

Provides endpoints for:
- Managing notification subscriptions
- Configuring notification preferences
- Server-Sent Events (SSE) for real-time notifications
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..models import NotificationConfig, NotificationSubscription
from ..notifications import get_notification_manager

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/subscribe", response_model=NotificationSubscription)
def subscribe(config: Optional[NotificationConfig] = None) -> NotificationSubscription:
    """Create a new notification subscription.
    
    Returns subscription with unique ID that should be stored client-side
    for subsequent requests.
    """
    manager = get_notification_manager()
    subscription_id = str(uuid.uuid4())[:8]  # Short UUID
    config = config or NotificationConfig()
    return manager.subscribe(subscription_id, config)


@router.get("/subscriptions", response_model=list[NotificationSubscription])
def list_subscriptions() -> list[NotificationSubscription]:
    """List all active notification subscriptions."""
    manager = get_notification_manager()
    return manager.list_subscriptions()


@router.get("/subscriptions/{subscription_id}", response_model=NotificationSubscription)
def get_subscription(subscription_id: str) -> NotificationSubscription:
    """Get specific subscription details."""
    manager = get_notification_manager()
    sub = manager.get_subscription(subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


@router.put("/subscriptions/{subscription_id}", response_model=NotificationSubscription)
def update_subscription(
    subscription_id: str,
    config: NotificationConfig
) -> NotificationSubscription:
    """Update notification configuration for existing subscription."""
    manager = get_notification_manager()
    sub = manager.update_config(subscription_id, config)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


@router.delete("/subscriptions/{subscription_id}")
def unsubscribe(subscription_id: str) -> dict:
    """Remove notification subscription."""
    manager = get_notification_manager()
    if manager.unsubscribe(subscription_id):
        return {"status": "unsubscribed", "subscription_id": subscription_id}
    raise HTTPException(status_code=404, detail="Subscription not found")


@router.get("/config/default", response_model=NotificationConfig)
def get_default_config() -> NotificationConfig:
    """Get default notification configuration.
    
    Use this as template when creating custom configurations.
    """
    return NotificationConfig()


@router.get("/types")
def get_notification_types() -> dict:
    """Get available notification types and their descriptions."""
    return {
        "REGRESSION_NEW": {
            "description": "Powiadomienie o nowej regresji",
            "icon": "🚨",
            "config_field": "regression_new"
        },
        "REGRESSION_DIFF": {
            "description": "Powiadomienie o kolejnej regresji w krótkim czasie (≤30s)",
            "icon": "⚠️",
            "config_field": "regression_diff"
        },
        "STATUS_TRANSITION": {
            "description": "Powiadomienie o zmianie stanu (dowolnej)",
            "icon": "🔄",
            "config_field": "status_transition"
        },
        "PASS_RECOVERY": {
            "description": "Powiadomienie o odzyskaniu (fail → pass)",
            "icon": "✅",
            "config_field": "pass_recovery"
        },
        "ANOMALY_NEW": {
            "description": "Powiadomienie o nowej anomalii",
            "icon": "🔶",
            "config_field": "anomaly_new"
        },
        "VISUAL_DIFF_NEW": {
            "description": "Powiadomienie o różnicy wizualnej",
            "icon": "👁️",
            "config_field": "visual_diff_new"
        },
        "HEALTH_CHANGE": {
            "description": "Powiadomienie o zmianie stanu zdrowia usługi",
            "icon": "💓",
            "config_field": "health_change"
        }
    }


@router.get("/status-transitions")
def get_status_transition_types() -> dict:
    """Get available status transition types."""
    return {
        "HEALTHY_TO_UNHEALTHY": {
            "description": "Zdrowy → Chory (poprawny → niepoprawny)",
            "example": "PASS → FAIL"
        },
        "UNHEALTHY_TO_HEALTHY": {
            "description": "Chory → Zdrowy (niepoprawny → poprawny)",
            "example": "FAIL → PASS"
        },
        "ANY": {
            "description": "Dowolna zmiana stanu",
            "example": "Dowolna zmiana statusu"
        }
    }


# SSE endpoint for real-time notifications
@router.get("/stream")
async def notification_stream(subscription_id: str = Query(..., description="Subscription ID")):
    """Server-Sent Events endpoint for real-time notifications.
    
    Connect to this endpoint to receive notifications in real-time.
    Requires active subscription.
    
    Example:
        const eventSource = new EventSource('/notifications/stream?subscription_id=abc123');
        eventSource.onmessage = (e) => {
            const notification = JSON.parse(e.data);
            // Show browser notification
        };
    """
    manager = get_notification_manager()
    sub = manager.get_subscription(subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Register SSE client
    queue = manager.register_sse_client(subscription_id)
    
    async def event_generator():
        """Generate SSE events."""
        try:
            # Send initial connection message
            yield f"data: {{\"type\": \"connected\", \"subscription_id\": \"{subscription_id}\"}}\n\n"
            
            last_index = 0
            while True:
                # Check for new notifications in queue
                if last_index < len(queue):
                    notifications = queue[last_index:]
                    for notif in notifications:
                        import json
                        data = json.dumps(notif.model_dump())
                        yield f"data: {data}\n\n"
                    last_index = len(queue)
                
                # Send heartbeat every 30 seconds to keep connection alive
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            # Clean up on disconnect
            manager.unregister_sse_client(subscription_id)
            raise
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/test")
def send_test_notification(
    subscription_id: str,
    background_tasks: BackgroundTasks
) -> dict:
    """Send a test notification to verify subscription works.
    
    The notification will be queued and sent via SSE if client is connected.
    """
    from ..models import NotificationPayload
    
    manager = get_notification_manager()
    sub = manager.get_subscription(subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    test_notification = NotificationPayload(
        notification_type="REGRESSION_NEW",
        title="🧪 Test powiadomienia",
        body="To jest testowe powiadomienie z wupbro. Jeśli je widzisz, konfiguracja działa poprawnie!",
        service="test-service",
        data={"test": True}
    )
    
    # Push to SSE queues
    manager.push_to_sse(test_notification)
    
    return {
        "status": "sent",
        "message": "Test notification queued for delivery"
    }
