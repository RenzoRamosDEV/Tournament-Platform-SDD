import django_filters
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.users.models import User
from apps.users.serializers.output import UserListSerializer, UserResponseSerializer


class UserFilterSet(django_filters.FilterSet):
    role = django_filters.ChoiceFilter(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ["role"]


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
