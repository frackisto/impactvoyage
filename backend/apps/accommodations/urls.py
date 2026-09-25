from rest_framework.routers import SimpleRouter

from .views import HotelViewSet, ResidenceViewSet

router = SimpleRouter()
router.register("hotels", HotelViewSet, basename="hotel")
router.register("residences", ResidenceViewSet, basename="residence")

urlpatterns = router.urls
