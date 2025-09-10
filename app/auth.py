from __future__ import annotations

from fastapi import Header, HTTPException, status
from typing import Optional

from .settings import settings

try:
    import jwt  # pyjwt
    HAVE_JWT = True
except ImportError:
    HAVE_JWT = False


def _unauthorized(detail: str = "Unauthorized"):
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


async def require_auth(authorization: Optional[str] = Header(default=None, alias="Authorization")):
    print("\n=== [AUTH DEBUG] ===")
    print(f"🔐 Incoming Header: {authorization}")
    print(f"🔐 Static Token Expected: {settings.AUTH_STATIC_BEARER_TOKEN}")
    print(f"🔐 JWT Secret Set: {bool(settings.AUTH_JWT_SECRET)}")

    if not settings.AUTH_STATIC_BEARER_TOKEN and not settings.AUTH_JWT_SECRET:
        print("✅ No auth required (none configured)")
        return

    if not authorization or not authorization.lower().startswith("bearer "):
        print("❌ Missing or invalid Authorization header format")
        _unauthorized("Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1].strip()
    print(f"🔑 Token Extracted: {token}")

    if settings.AUTH_STATIC_BEARER_TOKEN:
        if token == settings.AUTH_STATIC_BEARER_TOKEN:
            print("✅ Static token matched!")
            return
        else:
            print("❌ Static token does not match!")
            _unauthorized("Invalid token")

    if settings.AUTH_JWT_SECRET:
        if not HAVE_JWT:
            _unauthorized("JWT support not installed (pyjwt)")

        try:
            decode_kwargs = {"algorithms": ["HS256"]}
            if settings.AUTH_JWT_AUDIENCE:
                decode_kwargs["audience"] = settings.AUTH_JWT_AUDIENCE
            if settings.AUTH_JWT_ISSUER:
                decode_kwargs["issuer"] = settings.AUTH_JWT_ISSUER

            jwt.decode(token, settings.AUTH_JWT_SECRET, **decode_kwargs)
            print("✅ JWT verified successfully!")
            return
        except Exception as e:
            print(f"❌ JWT verification failed: {e}")
            _unauthorized("JWT verification failed")

    print("❌ Reached unexpected end of auth check")
    _unauthorized("Authorization failed")
