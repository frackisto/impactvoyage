from rest_framework.routers import SimpleRouter

from .views import BlogPostViewSet

router = SimpleRouter()
router.register("blog", BlogPostViewSet, basename="blogpost")

urlpatterns = router.urls
