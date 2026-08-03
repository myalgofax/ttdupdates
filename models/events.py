from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    BOOKING_OPEN = "BOOKING_OPEN"
    BOOKING_CLOSED = "BOOKING_CLOSED"
    WEBSITE_CHANGED = "WEBSITE_CHANGED"
    NEW_CALENDAR = "NEW_CALENDAR"
    NEW_NOTIFICATION = "NEW_NOTIFICATION"
    ERROR = "ERROR"
    BROWSER_RESTARTED = "BROWSER_RESTARTED"
    HEALTH_CHECK = "HEALTH_CHECK"


class BookingStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"


class Event(BaseModel):
    id: Optional[int] = None
    event_type: EventType
    message: str
    screenshot_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NewsItem(BaseModel):
    id: Optional[int] = None
    title: str
    url: Optional[str] = None
    content: Optional[str] = None
    source: str = "TTD"
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class SessionRecord(BaseModel):
    id: Optional[int] = None
    status: str
    auth_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class ScreenshotRecord(BaseModel):
    id: Optional[int] = None
    context: str
    file_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationRecord(BaseModel):
    id: Optional[int] = None
    channel: str
    message: str
    sent: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
