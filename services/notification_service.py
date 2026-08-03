from __future__ import annotations

import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from typing import Optional

from loguru import logger

from config.settings import AppConfig
from models.events import NotificationRecord
from services.database_service import DatabaseService

try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

try:
    from plyer import notification as desktop_notification
    DESKTOP_AVAILABLE = True
except ImportError:
    DESKTOP_AVAILABLE = False


class NotificationService:
    def __init__(self, config: AppConfig, db: DatabaseService) -> None:
        self._config = config
        self._db = db
        self._bot: Optional[object] = None
        if TELEGRAM_AVAILABLE and config.telegram_bot_token:
            self._bot = Bot(token=config.telegram_bot_token)

    async def notify(self, message: str, screenshot_path: Optional[str] = None) -> None:
        formatted = self._format_message(message, screenshot_path)
        if self._config.notifications.telegram:
            await self._send_telegram(formatted, screenshot_path)
        if self._config.notifications.desktop:
            self._send_desktop(message)
        if self._config.notifications.email:
            self._send_email(formatted)
        self._db.save_notification(NotificationRecord(channel="all", message=message,
                                                      sent=True, created_at=datetime.utcnow()))

    def _format_message(self, message: str, screenshot_path: Optional[str]) -> str:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        screenshot_info = "saved" if screenshot_path else "none"
        return (
            f"🔔 TTD Monitor\n\n"
            f"{message}\n\n"
            f"Time: {ts}\n"
            f"Screenshot: {screenshot_info}"
        )

    async def _send_telegram(self, message: str, screenshot_path: Optional[str]) -> None:
        if not TELEGRAM_AVAILABLE or not self._bot or not self._config.telegram_chat_id:
            return
        try:
            bot: Bot = self._bot  # type: ignore[assignment]
            await bot.send_message(chat_id=self._config.telegram_chat_id, text=message)
            if screenshot_path:
                with open(screenshot_path, "rb") as f:
                    await bot.send_photo(chat_id=self._config.telegram_chat_id, photo=f)
            logger.info("Telegram notification sent")
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")

    def _send_desktop(self, message: str) -> None:
        if not DESKTOP_AVAILABLE:
            return
        try:
            desktop_notification.notify(title="TTD Monitor", message=message[:255], timeout=10)
        except Exception as e:
            logger.warning(f"Desktop notification failed: {e}")

    def _send_email(self, message: str) -> None:
        if not all([self._config.email_sender, self._config.email_password, self._config.email_recipient]):
            return
        try:
            msg = MIMEText(message)
            msg["Subject"] = "TTD Monitor Alert"
            msg["From"] = self._config.email_sender
            msg["To"] = self._config.email_recipient
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self._config.email_sender, self._config.email_password)
                server.send_message(msg)
            logger.info("Email notification sent")
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
