from rest_framework import serializers

from apps.teams.models import Team, TeamMember


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
