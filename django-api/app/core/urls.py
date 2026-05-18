from rest_framework.routers import DefaultRouter

from core.views import (
    MatchViewSet,
    TeamMemberViewSet,
    TeamViewSet,
    TournamentTeamViewSet,
    TournamentViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"teams", TeamViewSet, basename="team")
router.register(r"team-members", TeamMemberViewSet, basename="teammember")
router.register(r"tournaments", TournamentViewSet, basename="tournament")
router.register(r"tournament-teams", TournamentTeamViewSet, basename="tournamentteam")
router.register(r"matches", MatchViewSet, basename="match")

urlpatterns = router.urls
