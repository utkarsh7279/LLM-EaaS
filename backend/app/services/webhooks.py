"""Webhook management and event notification system."""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

import aiohttp
from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Event types that can trigger webhooks."""

    EXPERIMENT_CREATED = "experiment.created"
    EXPERIMENT_COMPLETED = "experiment.completed"
    EXPERIMENT_FAILED = "experiment.failed"
    EVALUATION_STARTED = "evaluation.started"
    EVALUATION_COMPLETED = "evaluation.completed"
    RESULTS_READY = "results.ready"
    THRESHOLD_EXCEEDED = "threshold.exceeded"


@dataclass
class WebhookPayload:
    """Webhook event payload."""

    event_type: EventType
    timestamp: datetime
    experiment_id: str
    data: dict


class WebhookEndpoint:
    """Database model for webhook endpoints."""

    __tablename__ = "webhook_endpoints"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    events: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list of event types
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # For HMAC signature
    retry_policy: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # JSON
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class WebhookDeliveryLog:
    """Log of webhook deliveries for debugging."""

    __tablename__ = "webhook_delivery_logs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    webhook_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status_code: Mapped[Optional[int]] = mapped_column(nullable=True)
    response_time_ms: Mapped[Optional[int]] = mapped_column(nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class WebhookManager:
    """Manage and dispatch webhooks."""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries

    async def dispatch_webhook(
        self,
        event_type: EventType,
        experiment_id: str,
        data: dict,
        webhook_urls: list[str],
    ):
        """Dispatch webhook to multiple endpoints."""
        payload = WebhookPayload(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            experiment_id=experiment_id,
            data=data,
        )

        tasks = [self._send_webhook(url, payload) for url in webhook_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for url, result in zip(webhook_urls, results):
            if isinstance(result, Exception):
                logger.error(f"Webhook delivery failed for {url}: {result}")

    async def _send_webhook(self, url: str, payload: WebhookPayload, retry_count: int = 0) -> bool:
        """Send a single webhook with retry logic."""
        payload_dict = {
            "event_type": payload.event_type,
            "timestamp": payload.timestamp.isoformat(),
            "experiment_id": payload.experiment_id,
            "data": payload.data,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload_dict,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if 200 <= response.status < 300:
                        logger.info(f"Webhook delivered successfully to {url}")
                        return True
                    else:
                        raise Exception(f"HTTP {response.status}: {await response.text()}")

        except asyncio.TimeoutError:
            if retry_count < self.max_retries:
                await asyncio.sleep(2**retry_count)  # Exponential backoff
                return await self._send_webhook(url, payload, retry_count + 1)
            else:
                logger.error(f"Webhook timeout (max retries exceeded): {url}")
                return False

        except Exception as e:
            if retry_count < self.max_retries:
                await asyncio.sleep(2**retry_count)
                return await self._send_webhook(url, payload, retry_count + 1)
            else:
                logger.error(f"Webhook delivery failed (max retries exceeded) for {url}: {e}")
                return False


class WebhookEventBuilder:
    """Build common webhook event payloads."""

    @staticmethod
    def experiment_completed(
        experiment_id: str,
        mean_score: float,
        std_dev: float,
        item_count: int,
    ) -> dict:
        """Build experiment completed event."""
        return {
            "mean_score": mean_score,
            "std_dev": std_dev,
            "item_count": item_count,
            "completed_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def evaluation_started(experiment_id: str, total_items: int) -> dict:
        """Build evaluation started event."""
        return {
            "total_items": total_items,
            "started_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def threshold_exceeded(
        experiment_id: str,
        baseline_id: str,
        current_score: float,
        baseline_score: float,
        threshold: float,
    ) -> dict:
        """Build threshold exceeded event."""
        return {
            "baseline_experiment_id": baseline_id,
            "current_score": current_score,
            "baseline_score": baseline_score,
            "threshold": threshold,
            "difference": current_score - baseline_score,
            "detected_at": datetime.utcnow().isoformat(),
        }
