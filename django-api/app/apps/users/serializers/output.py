from rest_framework import serializers

from apps.users.models import User


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "role", "elo")


class UserResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "role", "elo", "avatar_url", "created_at")
        read_only_fields = ("id", "email", "elo", "avatar_url", "created_at")
