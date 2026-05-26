from rest_framework import serializers

from apps.teams.models import EloHistory, Team, TeamMember


class TeamListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ("id", "name", "owner", "created_at")


class TeamResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ("id", "name", "owner", "created_at")
        read_only_fields = ("id", "owner", "created_at")


class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = ("user", "team", "joined_at")
        read_only_fields = ("joined_at",)


class RankingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ("id", "name", "elo")


class TournamentRankingSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    elo_delta = serializers.IntegerField()


class EloHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EloHistory
        fields = ("id", "elo_before", "elo_after", "match_id", "created_at")
