from rest_framework.routers import DefaultRouter

from apps.tournaments.views import MatchViewSet, TournamentTeamViewSet, TournamentViewSet

router = DefaultRouter()
router.register(r"tournaments", TournamentViewSet, basename="tournament")
router.register(r"tournament-teams", TournamentTeamViewSet, basename="tournamentteam")
router.register(r"matches", MatchViewSet, basename="match")

urlpatterns = router.urls
