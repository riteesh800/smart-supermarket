"""
Simple API key authentication for destructive/expensive endpoints.
Reads SMARTMART_API_KEY from environment, defaults to 'dev-key' for local dev.
"""

import os
from fastapi import Header, HTTPException


API_KEY = os.environ.get("SMARTMART_API_KEY", "dev-key")


async def require_api_key(x_api_key: str = Header(default=None, alias="X-API-Key")):
    """FastAPI dependency: require a valid API key header for protected routes."""
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid API key. Set X-API-Key header."
        )
    return x_api_key
