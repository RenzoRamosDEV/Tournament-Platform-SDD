from rest_framework import serializers

from apps.teams.models import Team


class TeamCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ("name",)
