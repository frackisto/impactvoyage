from rest_framework.routers import SimpleRouter

from .views import VisaViewSet

router = SimpleRouter()
router.register("visas", VisaViewSet, basename="visa")

urlpatterns = router.urls
