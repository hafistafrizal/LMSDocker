from django.contrib.auth import get_user_model
from ninja.security import HttpBearer

from .tokens import decode_token


class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        claims = decode_token(token, "access")
        if claims is None:
            return None
        try:
            user_id = int(claims["sub"])
        except (TypeError, ValueError):
            return None
        return get_user_model().objects.filter(
            pk=user_id, is_active=True
        ).first()


jwt_auth = JWTAuth()
