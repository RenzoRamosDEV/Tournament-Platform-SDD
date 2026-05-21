from rest_framework import serializers

from apps.tournaments.models import Match, Tournament, TournamentTeam


class TournamentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ("id", "name", "status")


class TournamentResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ("id", "name", "status", "format", "max_teams", "start_date", "end_date", "created_by")
        read_only_fields = ("id", "created_by")

    def validate(self, data):
        start = data.get("start_date") or (self.instance.start_date if self.instance else None)
        end = data.get("end_date") or (self.instance.end_date if self.instance else None)
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "end_date must be >= start_date."})
        return data


class MatchListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = ("id", "tournament", "team_a", "team_b", "status")


class MatchResponseSerializer(serializers.ModelSerializer):
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


class TournamentTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentTeam
        fields = ("tournament", "team", "registered_at")
        read_only_fields = ("registered_at",)
