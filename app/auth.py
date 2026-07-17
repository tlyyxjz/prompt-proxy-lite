"""Bearer API key authentication with constant-time comparison."""

import secrets

from fastapi import Header, HTTPException, status

from app.config import settings


async def verify_client_key(authorization: str | None = Header(default=None)) -> str:
    """Validate the Bearer token against configured client keys."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Expected: Bearer <key>",
        )

    token = authorization[7:].strip()
    for configured in settings.client_keys:
        if secrets.compare_digest(token, configured):
            return token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
    )
