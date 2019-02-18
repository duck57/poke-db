from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # path('polls/', include('polls.urls')),  # leaving commented for later reference
    path('admin2/', admin.site.urls),
    path('city/', include('nestlist.urls', namespace='nestlist')),
    # path('species/', include('speciesinfo.urls', namespace='pokedex')),
    # path('cp/', include('pokeperfect.urls', namespace='perfect')),
    # path('type/', include('typeedit.urls', namespace='types'))
]
