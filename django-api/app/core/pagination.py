from rest_framework.pagination import CursorPagination


class MatchCursorPagination(CursorPagination):
    page_size = 20
    ordering = "-played_at"
