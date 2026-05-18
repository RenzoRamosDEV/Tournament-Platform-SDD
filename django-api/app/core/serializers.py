from rest_framework import serializers

from core.models import Match, Team, TeamMember, Tournament, TournamentTeam, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "role", "elo", "created_at")
        read_only_fields = ("id", "elo", "created_at")


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ("id", "name", "owner", "created_at")
        read_only_fields = ("id", "created_at")


class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = ("user", "team", "joined_at")
        read_only_fields = ("joined_at",)


class TournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ("id", "name", "status", "format", "max_teams", "start_date", "end_date")
        read_only_fields = ("id",)


class TournamentTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentTeam
        fields = ("tournament", "team", "registered_at")
        read_only_fields = ("registered_at",)


class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = (
            "id", "tournament", "team_a", "team_b", "winner_team",
            "score_a", "score_b", "status", "played_at",
        )
        read_only_fields = ("id",)

    def validate(self, data):
        winner = data.get("winner_team")
        if winner is None:
            return data
        team_a = data.get("team_a") or (self.instance.team_a if self.instance else None)
        team_b = data.get("team_b") or (self.instance.team_b if self.instance else None)
        if winner not in (team_a, team_b):
            raise serializers.ValidationError(
                {"winner_team": "winner_team must be team_a or team_b."}
            )
        return data
