from django.contrib import admin

from apps.users.models import EloHistory, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "role", "elo", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("username",)


@admin.register(EloHistory)
class EloHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "match", "elo_before", "elo_after", "changed_at")
