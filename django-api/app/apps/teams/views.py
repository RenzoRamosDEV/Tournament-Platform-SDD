import django_filters
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.teams.models import Team, TeamMember
from apps.teams.serializers.input import TeamCreateSerializer
from apps.teams.serializers.output import TeamListSerializer, TeamMemberSerializer, TeamResponseSerializer


class TeamFilterSet(django_filters.FilterSet):
    tournament_id = django_filters.NumberFilter(
        field_name="tournamentteam__tournament_id", lookup_expr="exact"
    )

    class Meta:
        model = Team
        fields = ["tournament_id"]


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
