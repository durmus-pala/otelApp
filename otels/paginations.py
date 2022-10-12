from rest_framework.pagination import PageNumberPagination


class OtelPagination(PageNumberPagination):
    page_size = 100


class OtelServiceCategoryPagination(PageNumberPagination):
    page_size = 1000
