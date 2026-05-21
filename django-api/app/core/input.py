from rest_framework import serializers

from core.models import Match, Team, Tournament, User


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "email", "password", "role")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class TeamCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ("name",)


class TournamentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ("name", "format", "max_teams", "start_date", "end_date")

    def validate(self, data):
        start = data.get("start_date")
        end = data.get("end_date")
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "end_date must be >= start_date."})
        return data


class MatchReportSerializer(serializers.Serializer):
    winner_id = serializers.IntegerField()
    score_team_a = serializers.IntegerField(min_value=0)
    score_team_b = serializers.IntegerField(min_value=0)

    def validate_winner_id(self, value):
        match = self.context.get("match")
        if match and value not in (match.team_a_id, match.team_b_id):
            raise serializers.ValidationError(
                "winner_id must be the id of team_a or team_b of this match."
            )
        return value
