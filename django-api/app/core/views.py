from rest_framework.viewsets import ModelViewSet

from core.models import Match, Team, TeamMember, Tournament, TournamentTeam, User
from core.serializers import (
    MatchSerializer,
    TeamMemberSerializer,
    TeamSerializer,
    TournamentSerializer,
    TournamentTeamSerializer,
    UserSerializer,
)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by("-elo")
    serializer_class = UserSerializer


class TeamViewSet(ModelViewSet):
    queryset = Team.objects.all().order_by("name")
    serializer_class = TeamSerializer


class TeamMemberViewSet(ModelViewSet):
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer


class TournamentViewSet(ModelViewSet):
    queryset = Tournament.objects.all().order_by("start_date")
    serializer_class = TournamentSerializer


class TournamentTeamViewSet(ModelViewSet):
    queryset = TournamentTeam.objects.all()
    serializer_class = TournamentTeamSerializer


class MatchViewSet(ModelViewSet):
    queryset = Match.objects.all().order_by("-played_at")
    serializer_class = MatchSerializer
