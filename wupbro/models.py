"""Pydantic models for wupbro events, driver requests, and notification config."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


EventType = Literal[
    "REGRESSION",
    "PASS",
    "ANOMALY",
    "VISUAL_DIFF",
    "HEALTH_TRANSITION",
]

NotificationType = Literal[
    "REGRESSION_NEW",  # Nowa regresja
    "REGRESSION_DIFF",  # Różnica w czasie (np. 30s)
    "STATUS_TRANSITION",  # Zmiana stanu (poprawny → niepoprawny, niepoprawny → poprawny)
    "ANOMALY_NEW",  # Nowa anomalia
    "VISUAL_DIFF_NEW",  # Nowa różnica wizualna
    "HEALTH_CHANGE",  # Zmiana stanu zdrowia usługi
    "PASS_RECOVERY",  # Odzyskanie po regresji (niepoprawny → poprawny)
]

# Typy przejść stanów dla filtracji
StatusTransitionType = Literal[
    "HEALTHY_TO_UNHEALTHY",  # Zdrowy → Chory (poprawny → niepoprawny)
    "UNHEALTHY_TO_HEALTHY",  # Chory → Zdrowy (niepoprawny → poprawny)
    "ANY",  # Dowolna zmiana stanu
]


class Event(BaseModel):
    """Generic WUP event posted by an agent."""

    type: EventType
    service: Optional[str] = None
    file: Optional[str] = None
    endpoint: Optional[str] = None
    url: Optional[str] = None
    status: Optional[str] = None
    stage: Optional[str] = None
    reason: Optional[str] = None
    diff: Optional[Dict[str, Any]] = None
    timestamp: int = Field(default_factory=lambda: int(time.time()))

    # Forward-compat: allow extra keys to land in `extra`
    model_config = {"extra": "allow"}


class EventList(BaseModel):
    items: List[Event]
    total: int


class DomDiffRequest(BaseModel):
    url: str
    service: str = "default"
    max_depth: int = 10


class ScreenshotRequest(BaseModel):
    url: str
    full_page: bool = True


class AnomalyReport(BaseModel):
    service: str
    metric: str
    value: float
    threshold: float
    timestamp: int = Field(default_factory=lambda: int(time.time()))


class NotificationConfig(BaseModel):
    """Konfiguracja powiadomień przeglądarkowych dla użytkownika."""
    
    # Globalne włączenie/wyłączenie powiadomień
    enabled: bool = True
    
    # Konfiguracja per typ powiadomienia
    regression_new: bool = True  # Powiadom o nowej regresji
    regression_diff: bool = False  # Powiadom o różnicy w czasie
    regression_diff_seconds: int = 30  # Okno czasowe dla różnicy (sekundy)
    
    status_transition: bool = True  # Powiadom o zmianie stanu
    status_transition_type: StatusTransitionType = "ANY"  # Które przejścia powiadamiać
    
    anomaly_new: bool = True  # Powiadom o nowej anomalii
    visual_diff_new: bool = False  # Powiadom o różnicy wizualnej
    health_change: bool = True  # Powiadom o zmianie stanu zdrowia
    pass_recovery: bool = True  # Powiadom o odzyskaniu (niepoprawny → poprawny)
    
    # Cooldown między powiadomieniami (unikanie spamu)
    cooldown_seconds: int = 5
    
    # Filtrowanie per serwis (puste = wszystkie serwisy)
    services_include: List[str] = []  # Tylko te serwisy (puste = wszystkie)
    services_exclude: List[str] = []  # Wyklucz te serwisy


class NotificationSubscription(BaseModel):
    """Subskrypcja powiadomień dla konkretnego klienta (przeglądarki)."""
    subscription_id: str  # Unikalny identyfikator subskrypcji
    config: NotificationConfig
    created_at: int = Field(default_factory=lambda: int(time.time()))
    last_notification_at: Optional[int] = None  # Ostatnie powiadomienie (do cooldown)


class NotificationPayload(BaseModel):
    """Payload wysyłany jako powiadomienie przeglądarkowe."""
    notification_type: NotificationType
    title: str
    body: str
    icon: Optional[str] = None
    service: Optional[str] = None
    event_type: Optional[EventType] = None
    timestamp: int = Field(default_factory=lambda: int(time.time()))
    data: Optional[Dict[str, Any]] = None  # Dodatkowe dane
