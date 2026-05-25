from rest_framework.routers import DefaultRouter

from apps.teams.views import TeamMemberViewSet, TeamViewSet

router = DefaultRouter()
router.register(r"teams", TeamViewSet, basename="team")
router.register(r"team-members", TeamMemberViewSet, basename="teammember")

urlpatterns = router.urls
