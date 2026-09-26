from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import AmenityListView, HotelViewSet, ResidenceViewSet

router = SimpleRouter()
router.register("hotels", HotelViewSet, basename="hotel")
router.register("residences", ResidenceViewSet, basename="residence")

urlpatterns = [path("amenities/", AmenityListView.as_view(), name="amenity-list"), *router.urls]
