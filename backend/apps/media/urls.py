from rest_framework.routers import SimpleRouter

from .views import AlbumViewSet

router = SimpleRouter()
router.register("media/albums", AlbumViewSet, basename="album")

urlpatterns = router.urls
