"""URLconf de test : backoffice à une adresse non standard (ADMIN_URL_PATH)."""
from django.contrib import admin
from django.urls import path

urlpatterns = [path("gestion-x7/", admin.site.urls)]
