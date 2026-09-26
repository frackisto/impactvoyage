from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from . import selectors
from .serializers import SearchParamsSerializer, SearchResponseSerializer, result_data


class SearchView(APIView):
    """
    Recherche globale (CdC § 7) : destinations, circuits, hébergements, véhicules,
    activités et événements publiés. /search/?q=dubai&type=tour,hotel&limit=24
    Les résultats de tous les types sont fusionnés et triés par pertinence.
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(parameters=[SearchParamsSerializer], responses=SearchResponseSerializer)
    def get(self, request):
        params = SearchParamsSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        data = params.validated_data
        found = selectors.search(data["q"], types=data.get("type"), destination=data.get("destination"))

        counts, results = {}, []
        for type_, (target, qs) in found.items():
            counts[type_] = qs.count()
            results += [result_data(target, obj, request) for obj in qs[: data["limit"]]]
        results.sort(key=lambda row: row["score"], reverse=True)
        return Response({
            "query": data["q"],
            "count": sum(counts.values()),
            "counts": counts,
            "results": results[: data["limit"]],
        })
