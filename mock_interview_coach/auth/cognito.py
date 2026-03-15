"""Cognito JWT validation and PKCE token exchange."""

import os
import json
import asyncio
import urllib.request
import urllib.parse
import urllib.error
from functools import lru_cache
from typing import Optional

from jose import jwt, JWTError


def is_cognito_configured() -> bool:
    """Return True only when all three Cognito env vars are set."""
    return all([
        os.getenv("COGNITO_USER_POOL_ID"),
        os.getenv("COGNITO_CLIENT_ID"),
        os.getenv("COGNITO_DOMAIN"),
    ])


@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    """Fetch Cognito JWKS once per process lifetime."""
    region = os.getenv("COGNITO_REGION", os.getenv("AWS_REGION", "us-east-1"))
    pool_id = os.getenv("COGNITO_USER_POOL_ID")
    url = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json"
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.loads(resp.read())


def validate_token(id_token: str, access_token: Optional[str] = None) -> dict:
    """Validate a Cognito id_token (RS256).

    Returns the decoded claims dict.
    Raises ValueError on any validation failure.
    """
    if not is_cognito_configured():
        raise ValueError("Cognito not configured")

    region = os.getenv("COGNITO_REGION", os.getenv("AWS_REGION", "us-east-1"))
    pool_id = os.getenv("COGNITO_USER_POOL_ID")
    client_id = os.getenv("COGNITO_CLIENT_ID")
    issuer = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"

    try:
        jwks = _get_jwks()
        kwargs = dict(algorithms=["RS256"], audience=client_id, issuer=issuer)
        if access_token:
            kwargs["access_token"] = access_token
        claims = jwt.decode(id_token, jwks, **kwargs)
        return claims
    except JWTError as exc:
        raise ValueError(f"Token validation failed: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"Token validation error: {exc}") from exc


def _exchange_code_sync(code: str, redirect_uri: str, code_verifier: str) -> dict:
    """Synchronous token exchange — called from asyncio executor."""
    domain = os.getenv("COGNITO_DOMAIN", "").rstrip("/")
    client_id = os.getenv("COGNITO_CLIENT_ID")

    params = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "client_id": client_id,
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }).encode()

    req = urllib.request.Request(
        f"{domain}/oauth2/token",
        data=params,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise ValueError(f"Token exchange failed ({exc.code}): {body}") from exc


async def exchange_code_for_tokens(
    code: str, redirect_uri: str, code_verifier: str
) -> dict:
    """Exchange an authorization code for Cognito tokens (async wrapper)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _exchange_code_sync, code, redirect_uri, code_verifier
    )
