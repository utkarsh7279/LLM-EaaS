"""API authentication and authorization utilities."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.api_key_models import APIKey, RateLimitLog

X_API_KEY = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return f"sk_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def verify_api_key(
    api_key: Optional[str] = Security(X_API_KEY),
    session: AsyncSession = Depends(get_session),
) -> APIKey:
    """Verify and return the API key, raise 403 if invalid."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing API key",
        )

    key_hash = hash_api_key(api_key)

    result = await session.execute(
        select(APIKey).where(
            and_(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True,
                or_condition(
                    APIKey.expires_at == None,
                    APIKey.expires_at > datetime.now(timezone.utc),
                ),
            )
        )
    )
    api_key_obj = result.scalar_one_or_none()

    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired API key",
        )

    # Update last used timestamp
    api_key_obj.last_used_at = datetime.now(timezone.utc)
    await session.commit()

    return api_key_obj


async def check_rate_limit(
    api_key: APIKey = Depends(verify_api_key),
    session: AsyncSession = Depends(get_session),
) -> APIKey:
    """Check if API key has exceeded rate limit."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=1)

    # Get or create rate limit log
    result = await session.execute(
        select(RateLimitLog).where(
            and_(
                RateLimitLog.api_key_id == api_key.id,
                RateLimitLog.window_start <= now,
                RateLimitLog.window_end >= now,
            )
        )
    )
    rate_log = result.scalar_one_or_none()

    if rate_log is None:
        rate_log = RateLimitLog(
            id=uuid4(),
            api_key_id=api_key.id,
            request_count=1,
            window_start=window_start,
            window_end=now + timedelta(hours=1),
        )
        session.add(rate_log)
    else:
        rate_log.request_count += 1

    await session.commit()

    if rate_log.request_count > api_key.rate_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {api_key.rate_limit} requests per hour",
            headers={"Retry-After": "3600"},
        )

    return api_key


def or_condition(*conditions):
    """Helper for OR conditions in SQLAlchemy."""
    from sqlalchemy import or_

    return or_(*conditions)
