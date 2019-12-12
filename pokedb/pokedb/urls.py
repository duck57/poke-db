from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin2/", admin.site.urls),
    path("pokedex/", include("speciesinfo.urls", namespace="pokedex")),
    # path("cp/", include("pokeperfect.urls", namespace="perfect")),
    path("city/", include("nestlist.urls", namespace="nestlist")),
]
