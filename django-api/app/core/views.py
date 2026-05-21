import django_filters
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from core.models import Match, Team, TeamMember, Tournament, TournamentTeam, User
from core.serializers import (
    MatchReportSerializer,
    MatchSerializer,
    TeamMemberSerializer,
    TeamSerializer,
    TournamentSerializer,
    TournamentTeamSerializer,
    UserSerializer,
)


class IsAdminRole(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == "admin"


class TournamentFilterSet(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Tournament.STATUS_CHOICES)

    class Meta:
        model = Tournament
        fields = ["status"]


class MatchFilterSet(django_filters.FilterSet):
    tournament_id = django_filters.NumberFilter(field_name="tournament_id")

    class Meta:
        model = Match
        fields = ["tournament_id"]


class UserViewSet(ReadOnlyModelViewSet):
    queryset = User.objects.all().order_by("-elo")
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class TeamViewSet(ModelViewSet):
    queryset = Team.objects.all().order_by("name")
    serializer_class = TeamSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TeamMemberViewSet(ModelViewSet):
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer


class TournamentViewSet(ModelViewSet):
    serializer_class = TournamentSerializer
    filterset_class = TournamentFilterSet
    http_method_names = ["get", "post", "head", "options"]

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

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TournamentTeamViewSet(ModelViewSet):
    queryset = TournamentTeam.objects.all()
    serializer_class = TournamentTeamSerializer


class MatchViewSet(ModelViewSet):
    serializer_class = MatchSerializer
    filterset_class = MatchFilterSet
    http_method_names = ["get", "post", "head", "options"]

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
        return Response(MatchSerializer(match).data, status=response_status)
