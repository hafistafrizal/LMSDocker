from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import RefreshSession, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Peran LMS", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Peran LMS", {"fields": ("role",)}),)
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = UserAdmin.list_filter + ("role",)


@admin.register(RefreshSession)
class RefreshSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "jti", "expires_at", "revoked_at")
    list_filter = ("revoked_at",)
    readonly_fields = ("user", "jti", "expires_at", "revoked_at", "created_at")
