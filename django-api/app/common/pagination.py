from rest_framework.pagination import CursorPagination, PageNumberPagination


class StandardPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100
    page_size_query_param = "page_size"


class MatchCursorPagination(CursorPagination):
    page_size = 20
    ordering = "-played_at"
