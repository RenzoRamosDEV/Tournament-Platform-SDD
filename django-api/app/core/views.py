import django_filters
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from core.input import MatchReportSerializer, TeamCreateSerializer, TournamentCreateSerializer
from core.models import Match, Team, TeamMember, Tournament, TournamentTeam, User
from core.output import (
    MatchListSerializer,
    MatchResponseSerializer,
    TeamListSerializer,
    TeamMemberSerializer,
    TeamResponseSerializer,
    TournamentListSerializer,
    TournamentResponseSerializer,
    TournamentTeamSerializer,
    UserListSerializer,
    UserResponseSerializer,
)
from core.pagination import MatchCursorPagination


class IsAdminRole(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == "admin"


class UserFilterSet(django_filters.FilterSet):
    role = django_filters.ChoiceFilter(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ["role"]


class TeamFilterSet(django_filters.FilterSet):
    tournament_id = django_filters.NumberFilter(
        field_name="tournamentteam__tournament_id", lookup_expr="exact"
    )

    class Meta:
        model = Team
        fields = ["tournament_id"]


class TournamentFilterSet(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Tournament.STATUS_CHOICES)

    class Meta:
        model = Tournament
        fields = ["status"]


class MatchFilterSet(django_filters.FilterSet):
    tournament_id = django_filters.NumberFilter(field_name="tournament_id")
    status = django_filters.ChoiceFilter(choices=Match.STATUS_CHOICES)

    class Meta:
        model = Match
        fields = ["tournament_id", "status"]


class UserViewSet(ReadOnlyModelViewSet):
    queryset = User.objects.all().order_by("-elo")
    serializer_class = UserResponseSerializer
    permission_classes = [AllowAny]
    filterset_class = UserFilterSet

    def filter_queryset(self, queryset):
        if self.request.query_params.get("role") and (
            not self.request.user.is_authenticated
            or getattr(self.request.user, "role", None) != "admin"
        ):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admins can filter by role.")
        return super().filter_queryset(queryset)


class TeamViewSet(ModelViewSet):
    queryset = Team.objects.all().order_by("name")
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
        out_serializer = TeamResponseSerializer(team)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)


class TeamMemberViewSet(ModelViewSet):
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer


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
        qs = Tournament.objects.all().order_by("start_date")
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
        return Match.objects.all().order_by("-played_at")

    def get_permissions(self):
        if self.action == "report":
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(detail=True, methods=["post"], url_path="report", url_name="report")
    def report(self, request, pk=None):
        try:
            match = Match.objects.get(pk=pk)
        except Match.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if match.status == "finished" and request.user.role != "admin":
            return Response(
                {"detail": "Match result already reported."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = MatchReportSerializer(
            data=request.data, context={"match": match}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        vd = serializer.validated_data
        is_overwrite = match.status == "finished"
        match.winner_team_id = vd["winner_id"]
        match.score_a = vd["score_team_a"]
        match.score_b = vd["score_team_b"]
        match.status = "finished"
        match.played_at = timezone.now()
        match.save()

        response_status = status.HTTP_200_OK if is_overwrite else status.HTTP_201_CREATED
        return Response(MatchResponseSerializer(match).data, status=response_status)
