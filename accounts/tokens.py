"""JWT issue and verification for short-lived access and rotating refresh tokens."""

from datetime import datetime, timezone as datetime_timezone
from uuid import uuid4

import jwt
from django.conf import settings

from .models import RefreshSession


def _new_token(user, token_type, lifetime):
    now = datetime.now(datetime_timezone.utc)
    jti = uuid4()
    exp = now + lifetime
    claims = {
        "sub": str(user.pk),
        "type": token_type,
        "iat": now,
        "nbf": now,
        "exp": exp,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "jti": str(jti),
    }
    token = jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, jti, exp


def create_token_pair(user):
    access, _, _ = _new_token(user, "access", settings.JWT_ACCESS_TTL)
    refresh, jti, exp = _new_token(user, "refresh", settings.JWT_REFRESH_TTL)
    RefreshSession.objects.create(user=user, jti=jti, expires_at=exp)
    return {"access": access, "refresh": refresh, "token_type": "bearer"}


def decode_token(token, expected_type):
    try:
        claims = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
            options={"require": ["sub", "type", "iat", "nbf", "exp", "iss", "aud", "jti"]},
        )
    except (jwt.PyJWTError, TypeError, ValueError):
        return None
    if claims.get("type") != expected_type:
        return None
    return claims
