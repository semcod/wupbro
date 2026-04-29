"""Notification manager for browser notifications.

Manages subscriptions, detects notification-worthy events, and sends
push notifications to subscribed browser clients.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from .models import (
    Event,
    EventType,
    NotificationConfig,
    NotificationPayload,
    NotificationSubscription,
    NotificationType,
    StatusTransitionType,
)
from .storage import EventStore


class NotificationManager:
    """Manages browser notification subscriptions and event detection."""

    def __init__(self, event_store: EventStore):
        self._store = event_store
        self._subscriptions: Dict[str, NotificationSubscription] = {}
        self._lock = threading.Lock()
        
        # Historia stanów zdrowia per serwis (do detekcji przejść)
        self._service_health: Dict[str, str] = {}  # service -> last_status
        
        # Historia regresji per serwis (do detekcji różnicy w czasie)
        self._last_regression_time: Dict[str, int] = {}  # service -> timestamp
        
        # Subskrypcje SSE (Server-Sent Events)
        self._sse_queues: Dict[str, List[NotificationPayload]] = defaultdict(list)

    def subscribe(self, subscription_id: str, config: NotificationConfig) -> NotificationSubscription:
        """Register a new notification subscription."""
        with self._lock:
            sub = NotificationSubscription(
                subscription_id=subscription_id,
                config=config
            )
            self._subscriptions[subscription_id] = sub
            return sub

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription. Returns True if found and removed."""
        with self._lock:
            if subscription_id in self._subscriptions:
                del self._subscriptions[subscription_id]
                return True
            return False

    def get_subscription(self, subscription_id: str) -> Optional[NotificationSubscription]:
        """Get subscription by ID."""
        with self._lock:
            return self._subscriptions.get(subscription_id)

    def list_subscriptions(self) -> List[NotificationSubscription]:
        """List all active subscriptions."""
        with self._lock:
            return list(self._subscriptions.values())

    def update_config(self, subscription_id: str, config: NotificationConfig) -> Optional[NotificationSubscription]:
        """Update configuration for existing subscription."""
        with self._lock:
            if subscription_id not in self._subscriptions:
                return None
            self._subscriptions[subscription_id].config = config
            return self._subscriptions[subscription_id]

    def process_event(self, event: Event) -> List[Tuple[str, NotificationPayload]]:
        """Process event and generate notifications for matching subscriptions.
        
        Returns list of (subscription_id, notification_payload) tuples.
        """
        notifications: List[Tuple[str, NotificationPayload]] = []
        
        with self._lock:
            current_time = int(time.time())
            service = event.service or "unknown"
            
            # Detekcja typów powiadomień dla tego zdarzenia
            detected_types = self._detect_notification_types(event, current_time)
            
            for sub_id, sub in self._subscriptions.items():
                if not sub.config.enabled:
                    continue
                    
                # Sprawdź cooldown
                if sub.last_notification_at:
                    elapsed = current_time - sub.last_notification_at
                    if elapsed < sub.config.cooldown_seconds:
                        continue
                
                # Sprawdź filtry serwisów
                if sub.config.services_include and service not in sub.config.services_include:
                    continue
                if service in sub.config.services_exclude:
                    continue
                
                # Generuj powiadomienia dla wykrytych typów
                for notif_type in detected_types:
                    if self._should_notify(notif_type, sub.config):
                        payload = self._create_payload(notif_type, event)
                        if payload:
                            notifications.append((sub_id, payload))
                            sub.last_notification_at = current_time
                            break  # One notification per event per subscription
        
        return notifications

    def _detect_notification_types(self, event: Event, current_time: int) -> List[NotificationType]:
        """Detect which notification types apply to this event."""
        detected: List[NotificationType] = []
        service = event.service or "unknown"
        
        event_type = event.type
        status = event.status or "unknown"
        
        # REGRESSION_NEW - nowa regresja
        if event_type == "REGRESSION":
            detected.append("REGRESSION_NEW")
            
            # Sprawdź różnicę w czasie (30s domyślnie)
            if service in self._last_regression_time:
                last_time = self._last_regression_time[service]
                diff = current_time - last_time
                if diff <= 30:  # Domyślnie 30s, będzie nadpisane przez config
                    detected.append("REGRESSION_DIFF")
            self._last_regression_time[service] = current_time
        
        # STATUS_TRANSITION - zmiana stanu
        if status != "unknown":
            last_status = self._service_health.get(service)
            if last_status and last_status != status:
                detected.append("STATUS_TRANSITION")
                
                # PASS_RECOVERY - odzyskanie (fail → pass)
                if last_status == "fail" and status == "pass":
                    detected.append("PASS_RECOVERY")
            self._service_health[service] = status
        elif event_type == "HEALTH_TRANSITION":
            detected.append("HEALTH_CHANGE")
        
        # ANOMALY_NEW
        if event_type == "ANOMALY":
            detected.append("ANOMALY_NEW")
        
        # VISUAL_DIFF_NEW
        if event_type == "VISUAL_DIFF":
            detected.append("VISUAL_DIFF_NEW")
        
        return detected

    def _should_notify(self, notif_type: NotificationType, config: NotificationConfig) -> bool:
        """Check if notification type should trigger based on config."""
        if notif_type == "REGRESSION_NEW":
            return config.regression_new
        elif notif_type == "REGRESSION_DIFF":
            return config.regression_diff
        elif notif_type == "STATUS_TRANSITION":
            return config.status_transition
        elif notif_type == "ANOMALY_NEW":
            return config.anomaly_new
        elif notif_type == "VISUAL_DIFF_NEW":
            return config.visual_diff_new
        elif notif_type == "HEALTH_CHANGE":
            return config.health_change
        elif notif_type == "PASS_RECOVERY":
            return config.pass_recovery
        return False

    def _create_payload(self, notif_type: NotificationType, event: Event) -> Optional[NotificationPayload]:
        """Create notification payload for the given type and event."""
        service = event.service or "unknown"
        
        payloads = {
            "REGRESSION_NEW": NotificationPayload(
                notification_type="REGRESSION_NEW",
                title=f"🚨 Regresja: {service}",
                body=f"Wykryto regresję: {event.reason or 'Brak szczegółów'}",
                service=service,
                event_type=event.type,
                data={"endpoint": event.endpoint, "file": event.file}
            ),
            "REGRESSION_DIFF": NotificationPayload(
                notification_type="REGRESSION_DIFF",
                title=f"⚠️ Kolejna regresja: {service}",
                body=f"Kolejna regresja w krótkim czasie (≤30s)",
                service=service,
                event_type=event.type,
                data={"endpoint": event.endpoint}
            ),
            "STATUS_TRANSITION": NotificationPayload(
                notification_type="STATUS_TRANSITION",
                title=f"🔄 Zmiana stanu: {service}",
                body=f"Status zmienił się na: {event.status}",
                service=service,
                event_type=event.type,
                data={"new_status": event.status}
            ),
            "PASS_RECOVERY": NotificationPayload(
                notification_type="PASS_RECOVERY",
                title=f"✅ Odzyskano: {service}",
                body=f"Usługa wróciła do stanu poprawnego",
                service=service,
                event_type=event.type,
                data={"status": event.status}
            ),
            "ANOMALY_NEW": NotificationPayload(
                notification_type="ANOMALY_NEW",
                title=f"🔶 Anomalia: {service}",
                body=f"Wykryto anomalię w metrykach",
                service=service,
                event_type=event.type
            ),
            "VISUAL_DIFF_NEW": NotificationPayload(
                notification_type="VISUAL_DIFF_NEW",
                title=f"👁️ Różnica wizualna: {service}",
                body=f"Wykryto zmiany w interfejsie użytkownika",
                service=service,
                event_type=event.type
            ),
            "HEALTH_CHANGE": NotificationPayload(
                notification_type="HEALTH_CHANGE",
                title=f"💓 Zdrowie usługi: {service}",
                body=f"Zmiana stanu zdrowia: {event.status}",
                service=service,
                event_type=event.type,
                data={"status": event.status}
            ),
        }
        
        return payloads.get(notif_type)

    # SSE (Server-Sent Events) support for real-time notifications
    def register_sse_client(self, client_id: str) -> List[NotificationPayload]:
        """Register a new SSE client and return its queue."""
        with self._lock:
            if client_id not in self._sse_queues:
                self._sse_queues[client_id] = []
            return self._sse_queues[client_id]

    def unregister_sse_client(self, client_id: str) -> None:
        """Remove an SSE client."""
        with self._lock:
            if client_id in self._sse_queues:
                del self._sse_queues[client_id]

    def push_to_sse(self, notification: NotificationPayload) -> None:
        """Push notification to all SSE clients."""
        with self._lock:
            for queue in self._sse_queues.values():
                queue.append(notification)


# Global notification manager instance
_notification_manager: Optional[NotificationManager] = None


def get_notification_manager(store: Optional[EventStore] = None) -> NotificationManager:
    """Get or create global notification manager."""
    global _notification_manager
    if _notification_manager is None:
        if store is None:
            from .storage import get_default_store
            store = get_default_store()
        _notification_manager = NotificationManager(store)
    return _notification_manager


def set_notification_manager(manager: NotificationManager) -> None:
    """Set global notification manager (for testing)."""
    global _notification_manager
    _notification_manager = manager
