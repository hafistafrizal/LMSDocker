from ninja import NinjaAPI

from accounts.api import router as auth_router
from accounts.auth import jwt_auth
from courses.api import router as courses_router

api = NinjaAPI(
    title="Simple LMS API",
    version="1.1.0",
    description="Praktikum PSS 7: JWT, RBAC, dan object permission",
    auth=jwt_auth,  # Melindungi seluruh endpoint secara global bawaan
)


# Public Endpoint (Bisa diakses tanpa token Bearer)
@api.get("/health", tags=["System"], auth=None)
def health(request):
    return {"status": "ok"}


# Router /auth tanpa Bearer global (router accounts mengelola auth secara internal)
api.add_router("/auth", auth_router)

# Router /courses terlindungi JWT
api.add_router("/courses", courses_router)