# courses/api.py
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from ninja import Router, Status

from .models import Course
from .schemas import CourseIn, CourseOut, CoursePatch, Message

router = Router(tags=["Courses"])
User = get_user_model()

@router.get("", response=list[CourseOut])
def list_courses(
    request,
    q: str | None = None,
    published: bool | None = None,
):
    qs = Course.objects.all().order_by("id")
    if q:
        qs = qs.filter(title__icontains=q)
    if published is not None:
        qs = qs.filter(is_published=published)
    return qs[:100]

@router.get(
    "/{course_id}",
    response={200: CourseOut, 404: Message},
)
def get_course(request, course_id: int):
    course = Course.objects.filter(pk=course_id).first()
    if course is None:
        return Status(404, {"detail": "Course tidak ditemukan"})
    return Status(200, course)

@router.post(
    "",
    response={201: CourseOut, 400: Message, 409: Message},
)
def create_course(request, payload: CourseIn):
    if not User.objects.filter(pk=payload.teacher_id).exists():
        return Status(400, {"detail": "teacher_id tidak terdaftar"})
    if Course.objects.filter(code=payload.code).exists():
        return Status(409, {"detail": "Kode Course sudah dipakai"})
    try:
        course = Course.objects.create(**payload.model_dump())
    except IntegrityError:
        return Status(409, {"detail": "Data berbenturan dengan database"})
    return Status(201, course)

@router.put(
    "/{course_id}",
    response={200: CourseOut, 400: Message,
              404: Message, 409: Message},
)
def replace_course(request, course_id: int, payload: CourseIn):
    course = Course.objects.filter(pk=course_id).first()
    if course is None:
        return Status(404, {"detail": "Course tidak ditemukan"})
    if not User.objects.filter(pk=payload.teacher_id).exists():
        return Status(400, {"detail": "teacher_id tidak terdaftar"})
    if Course.objects.exclude(pk=course_id).filter(
        code=payload.code
    ).exists():
        return Status(409, {"detail": "Kode Course sudah dipakai"})
    for field, value in payload.model_dump().items():
        setattr(course, field, value)
    try:
        course.save()
    except IntegrityError:
        return Status(409, {"detail": "Data berbenturan dengan database"})
    return Status(200, course)

@router.patch(
    "/{course_id}",
    response={200: CourseOut, 400: Message,
              404: Message, 409: Message},
)
def update_course(request, course_id: int, payload: CoursePatch):
    course = Course.objects.filter(pk=course_id).first()
    if course is None:
        return Status(404, {"detail": "Course tidak ditemukan"})
    changes = payload.model_dump(exclude_unset=True)
    if not changes or any(value is None for value in changes.values()):
        return Status(400, {"detail": "Field update tidak valid"})
    if "teacher_id" in changes and not User.objects.filter(
        pk=changes["teacher_id"]
    ).exists():
        return Status(400, {"detail": "teacher_id tidak terdaftar"})
    if "code" in changes and Course.objects.exclude(
        pk=course_id
    ).filter(code=changes["code"]).exists():
        return Status(409, {"detail": "Kode Course sudah dipakai"})
    for field, value in changes.items():
        setattr(course, field, value)
    try:
        course.save(update_fields=list(changes))
    except IntegrityError:
        return Status(409, {"detail": "Data berbenturan dengan database"})
    return Status(200, course)

@router.delete(
    "/{course_id}",
    response={204: None, 404: Message},
)
def delete_course(request, course_id: int):
    course = Course.objects.filter(pk=course_id).first()
    if course is None:
        return Status(404, {"detail": "Course tidak ditemukan"})
    course.delete()
    return Status(204, None)
