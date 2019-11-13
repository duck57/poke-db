from django.contrib import admin
from django.urls import include, path
from django.conf import settings

urlpatterns = [
    path("admin2/", admin.site.urls),
    path("pokedex/", include("speciesinfo.urls", namespace="pokedex")),
    # path('cp/', include('pokeperfect.urls', namespace='perfect')),
    path("city/", include("nestlist.urls", namespace="nestlist")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
        # For django versions before 2.0:
        # url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
