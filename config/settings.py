from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class BrowserConfig(BaseModel):
    headless: bool = False
    slow_mo: int = 100
    timeout: int = 30000
    viewport: dict = Field(default_factory=lambda: {"width": 1280, "height": 800})


class UrlsConfig(BaseModel):
    base: str
    login: str
    dashboard: str
    srivari_seva: str
    news_api: str


class PollingConfig(BaseModel):
    default_interval: int = 60
    near_release_interval: int = 30
    near_release_window_minutes: int = 60


class NotificationsConfig(BaseModel):
    telegram: bool = True
    desktop: bool = True
    email: bool = False


class LoggingConfig(BaseModel):
    level: str = "INFO"
    rotation: str = "10 MB"
    retention: str = "30 days"


class DatabaseConfig(BaseModel):
    path: str = "database/database.db"


class StorageConfig(BaseModel):
    auth_path: str = "storage/auth.json"
    cookies_path: str = "storage/cookies.json"


class SchedulerConfig(BaseModel):
    health_check_hour: int = 8
    health_check_minute: int = 0
    cleanup_hour: int = 2
    cleanup_minute: int = 0
    screenshot_retention_days: int = 7
    log_retention_days: int = 30


class AppConfig(BaseModel):
    browser: BrowserConfig
    urls: UrlsConfig
    polling: PollingConfig
    notifications: NotificationsConfig
    logging: LoggingConfig
    database: DatabaseConfig
    storage: StorageConfig
    scheduler: SchedulerConfig

    # Secrets from env
    username: str = Field(default_factory=lambda: os.getenv("TTD_USERNAME", ""))
    password: str = Field(default_factory=lambda: os.getenv("TTD_PASSWORD", ""))
    telegram_bot_token: str = Field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str = Field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))
    email_sender: str = Field(default_factory=lambda: os.getenv("EMAIL_SENDER", ""))
    email_password: str = Field(default_factory=lambda: os.getenv("EMAIL_PASSWORD", ""))
    email_recipient: str = Field(default_factory=lambda: os.getenv("EMAIL_RECIPIENT", ""))
    headless: bool = Field(default_factory=lambda: os.getenv("HEADLESS", "false").lower() == "true")


@lru_cache(maxsize=1)
def load_config() -> AppConfig:
    config_path = BASE_DIR / "config" / "config.yaml"
    with open(config_path) as f:
        raw = yaml.safe_load(f)

    # Override headless from env if set
    headless_env = os.getenv("HEADLESS")
    if headless_env is not None:
        raw["browser"]["headless"] = headless_env.lower() == "true"

    return AppConfig(**raw)
