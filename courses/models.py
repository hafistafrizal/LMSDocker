from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class CourseQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)


class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="courses_taught",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="Enrollment",
        related_name="joined_courses",
    )
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CourseQuerySet.as_manager()

    def __str__(self):
        return f"{self.code} - {self.title}"

    @property
    def students(self):
        """Bridge property agar tes PSS 7 yang memanggil students tetap berjalan."""
        return self.members


class Lesson(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
    )
    title = models.CharField(max_length=150)
    content = models.TextField()
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["course", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "order"],
                name="unique_lesson_order_per_course",
            )
        ]

    def __str__(self):
        return f"{self.order}. {self.title}"


class Assignment(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    title = models.CharField(max_length=150)
    deadline = models.DateTimeField()
    max_score = models.PositiveIntegerField(default=100)

    def is_overdue(self):
        return timezone.now() > self.deadline

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                name="unique_enrollment_per_student",
            )
        ]

    def __str__(self):
        return f"{self.student} / {self.course.code}"


class Submission(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submissions",
    )
    answer = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "student"],
                name="unique_submission_per_student",
            )
        ]

    def clean(self):
        super().clean()
        if self.assignment_id and self.score is not None:
            if self.score > self.assignment.max_score:
                raise ValidationError({
                    "score": "Skor melebihi nilai maksimum tugas."
                })

    def __str__(self):
        return f"{self.student} / {self.assignment.title}"