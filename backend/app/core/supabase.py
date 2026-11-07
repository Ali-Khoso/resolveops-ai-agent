"""Supabase credentials and authoritative token verification.

Always forward the verified end-user JWT to PostgREST; never use service_role.
"""
import os
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import urlsplit

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class SupabaseConfig:
    url: str
    publishable_key: str


@lru_cache(maxsize=1)
def get_config() -> SupabaseConfig:
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    parsed = urlsplit(url)
    if (not url or not key or parsed.scheme not in ("https", "http")
            or not parsed.netloc or parsed.username or parsed.password
            or (parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1"})):
        raise HTTPException(status_code=503, detail="Supabase is not configured. See backend/.env.example")
    return SupabaseConfig(url=url, publishable_key=key)


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str | None
    access_token: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    config = get_config()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{config.url}/auth/v1/user",
                headers={"apikey": config.publishable_key,
                         "Authorization": f"Bearer {credentials.credentials}"},
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail="Authentication service unavailable") from exc
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired session", headers={"WWW-Authenticate": "Bearer"})
    try:
        user = response.json()
        user_id = str(user["id"])
        from uuid import UUID
        UUID(user_id)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid user identity") from exc
    return CurrentUser(id=user_id, email=user.get("email"), access_token=credentials.credentials)
