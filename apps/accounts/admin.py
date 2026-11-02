from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Permission, Role, StoreMember, User, UserProfile


@admin.register(User)
class StoreProUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "phone",
        "status",
        "is_staff",
        "is_active",
    )
    search_fields = ("username", "email", "first_name", "last_name", "phone")
    list_filter = ("status", "is_staff", "is_active", "created_at")
    fieldsets = UserAdmin.fieldsets + (
        ("StorePro", {"fields": ("phone", "avatar", "status")}),
        ("Thời gian", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "is_system", "created_at")
    search_fields = ("name", "store__name")
    list_filter = ("is_system", "store")
    filter_horizontal = ("permissions",)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("code", "module", "name")
    search_fields = ("code", "module", "name")
    list_filter = ("module",)


@admin.register(StoreMember)
class StoreMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "store", "role", "status", "joined_at")
    search_fields = ("user__username", "user__email", "store__name")
    list_filter = ("store", "role", "status")


admin.site.register(UserProfile)
