from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from courses.models import Course, Enrollment, Lesson


class Command(BaseCommand):
    help = "Buat akun dan data kelas untuk pengujian JWT/RBAC (hanya praktikum lokal)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password", required=True,
            help="Password sementara semua akun demo; ganti jika dipakai di luar lab.",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        demo_users = [
            ("dosen_demo", User.Role.TEACHER),
            ("dosen_lain", User.Role.TEACHER),
            ("mahasiswa_demo", User.Role.STUDENT),
        ]
        users = {}
        for username, role in demo_users:
            user, _ = User.objects.get_or_create(username=username)
            user.role = role
            user.is_active = True
            user.set_password(options["password"])
            user.save(update_fields=["role", "is_active", "password"])
            users[username] = user

        course, _ = Course.objects.get_or_create(
            code="PSS-01",
            defaults={
                "title": "Pemrograman Sisi Server",
                "description": "Course untuk pengujian JWT",
                "teacher": users["dosen_demo"],
                "is_published": True,
            },
        )
        Course.objects.get_or_create(
            code="PSS-02",
            defaults={
                "title": "Course Dosen Lain",
                "description": "Untuk menguji ownership",
                "teacher": users["dosen_lain"],
                "is_published": True,
            },
        )
        Enrollment.objects.get_or_create(
            student=users["mahasiswa_demo"], course=course
        )
        Lesson.objects.get_or_create(
            course=course,
            order=1,
            defaults={"title": "Keamanan API", "content": "JWT dan RBAC"},
        )
        self.stdout.write(self.style.SUCCESS(
            "Data demo siap: dosen_demo, dosen_lain, mahasiswa_demo. "
            "Buat admin menggunakan createsuperuser."
        ))
