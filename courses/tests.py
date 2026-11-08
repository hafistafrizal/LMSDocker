import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from accounts.tokens import create_token_pair
from courses.models import Course, Enrollment


class SecurityApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.teacher = User.objects.create_user(
            username="teacher_test", password="correct-password",
            role="TEACHER",
        )
        cls.teacher_other = User.objects.create_user(
            username="teacher_other", password="correct-password",
            role="TEACHER",
        )
        cls.student = User.objects.create_user(
            username="student_test", password="correct-password",
            role="STUDENT",
        )
        cls.admin = User.objects.create_superuser(
            username="admin_test", password="correct-password"
        )
        cls.course = Course.objects.create(
            code="PSS-TEST", title="Keamanan API",
            teacher=cls.teacher, is_published=True,
        )
        cls.other_course = Course.objects.create(
            code="OTHER-TEST", title="Milik Dosen Lain",
            teacher=cls.teacher_other, is_published=True,
        )
        Enrollment.objects.create(student=cls.student, course=cls.course)

    def setUp(self):
        cache.clear()

    def access(self, user):
        return create_token_pair(user)["access"]

    def request(self, method, url, user=None, data=None, token=None):
        headers = {}
        if token is None and user is not None:
            token = self.access(user)
        if token is not None:
            headers["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        if data is None:
            return getattr(self.client, method)(url, **headers)
        return getattr(self.client, method)(
            url, data=json.dumps(data), content_type="application/json", **headers
        )

    def data(self):
        return {"code": "NEW-SEC", "title": "Course Baru", "description": "API", "is_published": False}

    def test_health_still_public(self):
        self.assertEqual(self.request("get", "/api/health").status_code, 200)

    def test_course_without_bearer_returns_401(self):
        self.assertEqual(self.request("get", "/api/courses").status_code, 401)

    def test_login_returns_access_and_refresh(self):
        response = self.request("post", "/api/auth/token", data={
            "username": "teacher_test", "password": "correct-password"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_wrong_password_returns_401(self):
        response = self.request("post", "/api/auth/token", data={
            "username": "teacher_test", "password": "wrong"
        })
        self.assertEqual(response.status_code, 401)

    def test_me_returns_current_identity(self):
        response = self.request("get", "/api/auth/me", user=self.teacher)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], "TEACHER")

    def test_profile_returns_only_public_identity_fields(self):
        response = self.request("get", "/api/auth/profile", user=self.teacher)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": self.teacher.pk,
                "username": self.teacher.username,
                "role": self.teacher.role,
            },
        )

    def test_profile_requires_valid_access_token(self):
        self.assertEqual(
            self.request("get", "/api/auth/profile").status_code, 401
        )
        refresh = create_token_pair(self.teacher)["refresh"]
        self.assertEqual(
            self.request("get", "/api/auth/profile", token=refresh).status_code,
            401,
        )

    def test_token_with_wrong_signature_returns_401(self):
        legit = self.access(self.teacher)
        claims = jwt.decode(legit, options={"verify_signature": False})
        forged = jwt.encode(claims, "different-long-secret-for-negative-tests-12345", algorithm="HS256")
        self.assertEqual(self.request("get", "/api/courses", token=forged).status_code, 401)

    def test_expired_token_returns_401(self):
        old = datetime.now(timezone.utc) - timedelta(hours=2)
        claims = {
            "sub": str(self.teacher.pk), "type": "access", "iat": old,
            "nbf": old, "exp": old + timedelta(minutes=10),
            "iss": settings.JWT_ISSUER, "aud": settings.JWT_AUDIENCE,
            "jti": str(uuid4()),
        }
        expired = jwt.encode(claims, settings.JWT_SECRET, algorithm="HS256")
        self.assertEqual(self.request("get", "/api/courses", token=expired).status_code, 401)

    def test_refresh_cannot_access_course(self):
        refresh = create_token_pair(self.teacher)["refresh"]
        self.assertEqual(self.request("get", "/api/courses", token=refresh).status_code, 401)

    def test_access_cannot_refresh(self):
        access = self.access(self.teacher)
        response = self.request("post", "/api/auth/refresh", data={"refresh": access})
        self.assertEqual(response.status_code, 401)

    def test_refresh_rotates_and_replay_fails(self):
        refresh = create_token_pair(self.teacher)["refresh"]
        first = self.request("post", "/api/auth/refresh", data={"refresh": refresh})
        self.assertEqual(first.status_code, 200, first.content)
        second = self.request("post", "/api/auth/refresh", data={"refresh": refresh})
        self.assertEqual(second.status_code, 401)

    def test_logout_revokes_refresh(self):
        tokens = create_token_pair(self.teacher)
        result = self.request("post", "/api/auth/logout", token=tokens["access"], data={
            "refresh": tokens["refresh"]
        })
        self.assertEqual(result.status_code, 204)
        after = self.request("post", "/api/auth/refresh", data={"refresh": tokens["refresh"]})
        self.assertEqual(after.status_code, 401)

    def test_student_can_only_list_enrolled_course(self):
        response = self.request("get", "/api/courses", user=self.student)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([x["code"] for x in response.json()], ["PSS-TEST"])

    def test_student_cannot_view_unenrolled_course(self):
        response = self.request("get", f"/api/courses/{self.other_course.pk}", user=self.student)
        self.assertEqual(response.status_code, 404)

    def test_teacher_only_lists_own_course(self):
        response = self.request("get", "/api/courses", user=self.teacher)
        self.assertEqual([x["code"] for x in response.json()], ["PSS-TEST"])

    def test_admin_lists_all_courses(self):
        response = self.request("get", "/api/courses", user=self.admin)
        self.assertEqual(len(response.json()), 2)

    def test_student_cannot_post(self):
        response = self.request("post", "/api/courses", user=self.student, data=self.data())
        self.assertEqual(response.status_code, 403)

    def test_teacher_post_derives_owner_from_token(self):
        payload = self.data()
        payload["teacher_id"] = self.teacher_other.pk  # field tidak boleh dipercaya
        response = self.request("post", "/api/courses", user=self.teacher, data=payload)
        self.assertEqual(response.status_code, 201, response.content)
        created = Course.objects.get(code="NEW-SEC")
        self.assertEqual(created.teacher_id, self.teacher.pk)

    def test_teacher_can_patch_own_course(self):
        response = self.request(
            "patch", f"/api/courses/{self.course.pk}", user=self.teacher,
            data={"title": "Revisi Guru"}
        )
        self.assertEqual(response.status_code, 200, response.content)

    def test_teacher_cannot_patch_other_course(self):
        response = self.request(
            "patch", f"/api/courses/{self.other_course.pk}", user=self.teacher,
            data={"title": "Tidak Boleh"}
        )
        self.assertEqual(response.status_code, 404)

    def test_teacher_cannot_delete(self):
        response = self.request("delete", f"/api/courses/{self.course.pk}", user=self.teacher)
        self.assertEqual(response.status_code, 403)

    def test_admin_can_delete(self):
        response = self.request("delete", f"/api/courses/{self.other_course.pk}", user=self.admin)
        self.assertEqual(response.status_code, 204)

    def test_revoked_user_role_takes_effect_immediately(self):
        token = self.access(self.teacher)
        self.teacher.role = "STUDENT"
        self.teacher.save(update_fields=["role"])
        response = self.request("post", "/api/courses", token=token, data=self.data())
        self.assertEqual(response.status_code, 403)

    def test_inactive_user_token_returns_401(self):
        token = self.access(self.teacher)
        self.teacher.is_active = False
        self.teacher.save(update_fields=["is_active"])
        self.assertEqual(self.request("get", "/api/courses", token=token).status_code, 401)

    def test_login_rate_limited(self):
        status_codes = []
        for _ in range(6):
            response = self.request("post", "/api/auth/token", data={
                "username": "teacher_test", "password": "wrong"
            })
            status_codes.append(response.status_code)
        self.assertEqual(status_codes[:5], [401] * 5)
        self.assertEqual(status_codes[5], 429)

    def test_student_cannot_patch_course(self):
        # 1. Login sebagai mahasiswa untuk mendapatkan token
        # Sesuaikan username dan password dengan akun dummy di setUp milikmu
        login_resp = self.client.post(
            "/api/auth/token",
            data={"username": "mhs1", "password": "student123"},
            content_type="application/json"
        )
        self.assertEqual(login_resp.status_code, 200, "Login mahasiswa gagal")
        token = login_resp.json()["access"]

        # 2. Siapkan header dengan Bearer Token
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

        # 3. Lakukan request PATCH ke course (asumsi course ID 1 sudah terbuat di setUp)
        # Jika di setUp milikmu nama variabelnya self.course, ganti angka 1 dengan self.course.id
        payload = {"title": "Mencoba ganti judul"}
        patch_resp = self.client.patch(
            "/api/courses/1", 
            data=payload,
            content_type="application/json",
            **headers
        )

        # 4. Pastikan sistem menolak dengan 403 Forbidden
        self.assertEqual(patch_resp.status_code, 403)