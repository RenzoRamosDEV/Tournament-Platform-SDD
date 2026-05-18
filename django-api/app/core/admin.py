from django.contrib import admin

from core.models import Match, Team, TeamMember, Tournament, TournamentTeam, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "role", "elo", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("username",)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")
    search_fields = ("name",)


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "team", "joined_at")


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "format", "max_teams", "start_date", "end_date")
    list_filter = ("status", "format")
    search_fields = ("name",)


@admin.register(TournamentTeam)
class TournamentTeamAdmin(admin.ModelAdmin):
    list_display = ("tournament", "team", "registered_at")


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("tournament", "team_a", "team_b", "status", "score_a", "score_b", "played_at")
    list_filter = ("status",)
