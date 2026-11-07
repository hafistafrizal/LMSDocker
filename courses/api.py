from typing import List, Optional
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router

from accounts.models import User
from courses.models import Course
from courses.permissions import require_role
from courses.schemas import CourseIn, CoursePatchIn, CourseOut

router = Router(tags=["Courses"])


@router.get("", response=List[CourseOut])
def list_courses(
    request, q: Optional[str] = None, is_published: Optional[bool] = None
):
    user = request.auth
    queryset = Course.objects.all()

    # Filter RBAC PSS 7
    if user.role == User.Role.TEACHER:
        queryset = queryset.filter(teacher=user)
    elif user.role == User.Role.STUDENT:
        queryset = queryset.filter(is_published=True, enrollments__student=user)

    if q:
        queryset = queryset.filter(
            Q(title__icontains=q) | Q(description__icontains=q)
        )
    if is_published is not None:
        queryset = queryset.filter(is_published=is_published)

    return queryset


@router.get("/{course_id}", response=CourseOut)
def get_course(request, course_id: int):
    user = request.auth
    queryset = Course.objects.all()

    if user.role == User.Role.TEACHER:
        queryset = queryset.filter(teacher=user)
    elif user.role == User.Role.STUDENT:
        queryset = queryset.filter(is_published=True, enrollments__student=user)

    return get_object_or_404(queryset, pk=course_id)


@router.post("", response={201: CourseOut})
def create_course(request, payload: CourseIn):
    require_role(request.auth, User.Role.TEACHER, User.Role.ADMIN)

    # Pemilik course otomatis diambil dari token autentikasi PSS 7
    course = Course.objects.create(**payload.model_dump(), teacher=request.auth)
    return 201, course


@router.patch("/{course_id}", response=CourseOut)
def update_course(request, course_id: int, payload: CoursePatchIn):
    require_role(request.auth, User.Role.TEACHER, User.Role.ADMIN)

    queryset = Course.objects.all()
    if request.auth.role == User.Role.TEACHER:
        queryset = queryset.filter(teacher=request.auth)

    course = get_object_or_404(queryset, pk=course_id)

    for attr, value in payload.model_dump(exclude_unset=True).items():
        setattr(course, attr, value)

    course.save()
    return course


@router.delete("/{course_id}", response={204: None})
def delete_course(request, course_id: int):
    require_role(request.auth, User.Role.ADMIN)

    course = get_object_or_404(Course, pk=course_id)
    course.delete()
    return 204, None