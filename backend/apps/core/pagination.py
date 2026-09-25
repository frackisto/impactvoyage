"""
Pagination par défaut de l'API. Module séparé de core.api : DRF charge cette
classe pendant l'import de ses propres ViewSets (import circulaire sinon).
"""
from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """12 éléments par page ; ?page_size= plafonné à 48."""

    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 48
