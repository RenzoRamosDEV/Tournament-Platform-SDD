from django.contrib import admin

from apps.tournaments.models import Match, Tournament, TournamentTeam


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
