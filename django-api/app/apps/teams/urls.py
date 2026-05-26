from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.teams.views import RankingListView, TeamEloHistoryView, TeamMemberViewSet, TeamViewSet

router = DefaultRouter()
router.register(r"teams", TeamViewSet, basename="team")
router.register(r"team-members", TeamMemberViewSet, basename="teammember")

urlpatterns = router.urls + [
    path("rankings/", RankingListView.as_view(), name="rankings"),
    path("teams/<int:pk>/elo-history/", TeamEloHistoryView.as_view(), name="team-elo-history"),
]
