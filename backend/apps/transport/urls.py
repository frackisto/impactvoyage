from rest_framework.routers import SimpleRouter

from .views import TransportViewSet

router = SimpleRouter()
router.register("transport", TransportViewSet, basename="transport")

urlpatterns = router.urls
