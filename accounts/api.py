from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.utils import timezone
from ninja import Router, Status
from ninja.errors import HttpError
from ninja.throttling import AnonRateThrottle

from .auth import jwt_auth
from .models import RefreshSession
from .schemas import LoginIn, MeOut, RefreshIn, TokenOut, ProfileOut, ChangePasswordIn
from .tokens import create_token_pair, decode_token

router = Router(tags=["Authentication"], auth=None)

@router.post("/token", response=TokenOut, throttle=[AnonRateThrottle("5/m")])
def obtain_token(request, payload: LoginIn):
    user = authenticate(
        request=request,
        username=payload.username,
        password=payload.password,
    )
    if user is None or not user.is_active:
        raise HttpError(401, "Username atau password salah")
    return create_token_pair(user)

@router.post("/refresh", response=TokenOut, throttle=[AnonRateThrottle("20/m")])
def refresh_token(request, payload: RefreshIn):
    claims = decode_token(payload.refresh, "refresh")
    if claims is None:
        raise HttpError(401, "Refresh token tidak valid")

    with transaction.atomic():
        session = RefreshSession.objects.select_for_update().filter(
            jti=claims["jti"], user_id=claims["sub"]
        ).first()
        if session is None or session.revoked_at or session.expires_at <= timezone.now():
            raise HttpError(401, "Refresh token tidak valid atau sudah dipakai")
        user = get_user_model().objects.filter(
            pk=claims["sub"], is_active=True
        ).first()
        if user is None:
            raise HttpError(401, "Refresh token tidak valid")
        session.revoked_at = timezone.now()
        session.save(update_fields=["revoked_at"])
        return create_token_pair(user)

@router.get("/me", response=MeOut, auth=jwt_auth)
def who_am_i(request):
    return request.auth

@router.post("/logout", response={204: None, 401: dict}, auth=jwt_auth)
def logout(request, payload: RefreshIn):
    claims = decode_token(payload.refresh, "refresh")
    if claims is None or str(request.auth.pk) != claims["sub"]:
        return Status(401, {"detail": "Refresh token tidak valid"})
    RefreshSession.objects.filter(
        jti=claims["jti"], user=request.auth, revoked_at__isnull=True
    ).update(revoked_at=timezone.now())
    return Status(204, None)

@router.get("/profile", response=ProfileOut, auth=jwt_auth)
def get_profile(request):
    return request.auth

@router.post("/change-password", response={200: dict, 400: dict}, auth=jwt_auth)
def change_password(request, payload: ChangePasswordIn):
    user = request.auth
    
    # 1. Validasi password lama
    if not user.check_password(payload.old_password):
        return 400, {"detail": "Password lama salah"}
    
    # 2. Ganti dan simpan password baru
    user.set_password(payload.new_password)
    user.save()
    
    # 3. Keamanan Tambahan: Cabut semua refresh session yang sedang aktif
    RefreshSession.objects.filter(
        user=user, revoked_at__isnull=True
    ).update(revoked_at=timezone.now())
    
    return 200, {"detail": "Password berhasil diubah"}