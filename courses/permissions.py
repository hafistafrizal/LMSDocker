from ninja.errors import HttpError

from accounts.models import User
from .models import Course


def require_role(user, *allowed_roles):
    if user.role not in allowed_roles:
        raise HttpError(403, "Anda tidak memiliki izin untuk aksi ini")


def visible_courses(user):
    qs = Course.objects.all()
    if user.role == User.Role.ADMIN:
        return qs
    if user.role == User.Role.TEACHER:
        return qs.filter(teacher=user)
    return qs.filter(
        is_published=True,
        enrollments__student=user,
    ).distinct()


def course_for_read(user, course_id):
    course = visible_courses(user).filter(pk=course_id).first()
    if course is None:
        raise HttpError(404, "Course tidak ditemukan")
    return course


def course_for_write(user, course_id):
    require_role(user, User.Role.TEACHER, User.Role.ADMIN)
    qs = Course.objects.all()
    if user.role == User.Role.TEACHER:
        qs = qs.filter(teacher=user)
    course = qs.filter(pk=course_id).first()
    if course is None:
        raise HttpError(404, "Course tidak ditemukan")
    return course
