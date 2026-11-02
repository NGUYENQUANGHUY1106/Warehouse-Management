from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "store", "type", "title", "is_read", "created_at")
    search_fields = ("title", "message", "user__username")
    list_filter = ("store", "type", "is_read", "created_at")
