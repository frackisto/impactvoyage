from rest_framework.routers import SimpleRouter

from .views import DestinationViewSet

router = SimpleRouter()
router.register("destinations", DestinationViewSet, basename="destination")

urlpatterns = router.urls
