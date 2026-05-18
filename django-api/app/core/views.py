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
    queryset = User.objects.all()
    serializer_class = UserSerializer


class TeamViewSet(ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


class TeamMemberViewSet(ModelViewSet):
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer


class TournamentViewSet(ModelViewSet):
    queryset = Tournament.objects.all()
    serializer_class = TournamentSerializer


class TournamentTeamViewSet(ModelViewSet):
    queryset = TournamentTeam.objects.all()
    serializer_class = TournamentTeamSerializer


class MatchViewSet(ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
