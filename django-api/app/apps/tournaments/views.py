import django_filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.tournaments.models import Match, Tournament, TournamentTeam
from apps.tournaments.serializers.input import MatchReportSerializer, TournamentCreateSerializer
from apps.tournaments.serializers.output import (
    MatchListSerializer,
    MatchResponseSerializer,
    TournamentListSerializer,
    TournamentResponseSerializer,
    TournamentTeamSerializer,
)
from common.pagination import MatchCursorPagination
from common.permissions import IsAdminRole


class TournamentFilterSet(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Tournament.STATUS_CHOICES)
    date_from = django_filters.DateFilter(field_name="start_date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="start_date", lookup_expr="lte")
    created_by = django_filters.NumberFilter(field_name="created_by_id")

    class Meta:
        model = Tournament
        fields = ["status", "date_from", "date_to", "created_by"]


class MatchFilterSet(django_filters.FilterSet):
    tournament_id = django_filters.NumberFilter(field_name="tournament_id")
    status = django_filters.ChoiceFilter(choices=Match.STATUS_CHOICES)
    date_from = django_filters.DateFilter(field_name="played_at", lookup_expr="date__gte")
    date_to = django_filters.DateFilter(field_name="played_at", lookup_expr="date__lte")

    class Meta:
        model = Match
        fields = ["tournament_id", "status", "date_from", "date_to"]


class TournamentViewSet(ModelViewSet):
    filterset_class = TournamentFilterSet
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return TournamentCreateSerializer
        if self.action == "list":
            return TournamentListSerializer
        return TournamentResponseSerializer

    def get_queryset(self):
        qs = Tournament.objects.prefetch_related("tournamentteam_set").all().order_by("start_date")
        user = self.request.user
        if user.is_authenticated and getattr(user, "role", None) in ("admin", "organizer"):
            return qs
        return qs.exclude(status="draft")

    def get_permissions(self):
        if self.action == "create":
            return [IsAdminRole()]
        return [AllowAny()]

    def create(self, request, *args, **kwargs):
        in_serializer = TournamentCreateSerializer(data=request.data)
        in_serializer.is_valid(raise_exception=True)
        tournament = in_serializer.save(created_by=request.user)

        from django.db import transaction
        import events.producer as _producer

        payload = {
            "tournament_id": tournament.id,
            "name": tournament.name,
            "created_at": tournament.start_date.isoformat(),
        }
        transaction.on_commit(lambda: _producer.publish_event("tournament.created", payload))

        out_serializer = TournamentResponseSerializer(tournament)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)


class TournamentTeamViewSet(ModelViewSet):
    queryset = TournamentTeam.objects.all()
    serializer_class = TournamentTeamSerializer


class MatchViewSet(ModelViewSet):
    filterset_class = MatchFilterSet
    pagination_class = MatchCursorPagination
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        if self.action == "list":
            return MatchListSerializer
        return MatchResponseSerializer

    def get_queryset(self):
        return Match.objects.select_related("tournament").prefetch_related("team_a", "team_b").all().order_by("-played_at")

    def get_permissions(self):
        if self.action == "report":
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(detail=True, methods=["post"], url_path="report", url_name="report")
    def report(self, request, pk=None):
        from apps.tournaments.services import MatchService, MatchAlreadyFinished

        try:
            match = Match.objects.get(pk=pk)
        except Match.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = MatchReportSerializer(
            data=request.data, context={"match": match}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        vd = serializer.validated_data
        is_admin = getattr(request.user, "role", None) == "admin"
        is_overwrite = match.status == "finished"

        try:
            match = MatchService.report_result(
                match.id, vd["winner_id"], vd["score_team_a"], vd["score_team_b"],
                is_admin=is_admin,
            )
        except MatchAlreadyFinished:
            return Response(
                {"detail": "Match result already reported."},
                status=status.HTTP_409_CONFLICT,
            )

        response_status = status.HTTP_200_OK if is_overwrite else status.HTTP_201_CREATED
        return Response(MatchResponseSerializer(match).data, status=response_status)
