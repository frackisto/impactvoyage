from rest_framework.routers import SimpleRouter

from .views import ContactMessageViewSet, QuoteViewSet

router = SimpleRouter()
router.register("quotes", QuoteViewSet, basename="quote")
router.register("contact", ContactMessageViewSet, basename="contact")

urlpatterns = router.urls
