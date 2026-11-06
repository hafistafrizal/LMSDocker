# config/api.py
from ninja import NinjaAPI
from courses.api import router as courses_router

api = NinjaAPI(
    title="Simple LMS API",
    version="1.0.0",
    description="Praktikum REST API PSS 6",
)

@api.get("/health", tags=["System"])
def health(request):
    return {"status": "ok"}

api.add_router("/courses", courses_router)
