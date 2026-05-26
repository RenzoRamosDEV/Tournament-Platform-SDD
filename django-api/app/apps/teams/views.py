import django_filters
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.teams.models import EloHistory, Team, TeamMember
from apps.teams.serializers.input import TeamCreateSerializer
from apps.teams.serializers.output import (
    EloHistorySerializer,
    RankingSerializer,
    TeamListSerializer,
    TeamMemberSerializer,
    TeamResponseSerializer,
    TournamentRankingSerializer,
)
from common.pagination import StandardPagination


class TeamFilterSet(django_filters.FilterSet):
    tournament_id = django_filters.NumberFilter(
        field_name="tournamentteam__tournament_id", lookup_expr="exact"
    )

    class Meta:
        model = Team
        fields = ["tournament_id"]


class TeamViewSet(ModelViewSet):
    queryset = Team.objects.prefetch_related("tournamentteam_set", "teammember_set").all().order_by("name")
    filterset_class = TeamFilterSet
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return TeamCreateSerializer
        if self.action == "list":
            return TeamListSerializer
        return TeamResponseSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        return [AllowAny()]

    def create(self, request, *args, **kwargs):
        in_serializer = TeamCreateSerializer(data=request.data)
        in_serializer.is_valid(raise_exception=True)
        team = in_serializer.save(owner=request.user)

        from django.db import transaction
        import events.producer as _producer

        payload = {
            "team_id": team.id,
            "name": team.name,
            "created_at": team.created_at.isoformat(),
        }
        transaction.on_commit(lambda: _producer.publish_event("team.created", payload))

        out_serializer = TeamResponseSerializer(team)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)


class TeamMemberViewSet(ModelViewSet):
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer


class RankingListView(ListAPIView):
    permission_classes = [AllowAny]
    pagination_class = StandardPagination

    def get_queryset(self):
        tournament_id = self.request.query_params.get("tournament_id")
        if tournament_id:
            return []  # handled in list()
        return Team.objects.order_by("-elo")

    def get_serializer_class(self):
        tournament_id = self.request.query_params.get("tournament_id")
        if tournament_id:
            return TournamentRankingSerializer
        return RankingSerializer

    def list(self, request, *args, **kwargs):
        tournament_id = request.query_params.get("tournament_id")
        if tournament_id:
            qs = (
                EloHistory.objects.filter(match__tournament_id=tournament_id)
                .values("team_id", "team__name")
                .annotate(elo_delta=Sum(F("elo_after") - F("elo_before")))
                .order_by("-elo_delta")
            )
            data = [
                {"id": row["team_id"], "name": row["team__name"], "elo_delta": row["elo_delta"]}
                for row in qs
            ]
            page = self.paginate_queryset(data)
            if page is not None:
                serializer = TournamentRankingSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = TournamentRankingSerializer(data, many=True)
            return Response(serializer.data)
        return super().list(request, *args, **kwargs)


class TeamEloHistoryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        get_object_or_404(Team, pk=pk)
        history = EloHistory.objects.filter(team_id=pk).order_by("-created_at")
        serializer = EloHistorySerializer(history, many=True)
        return Response(serializer.data)
