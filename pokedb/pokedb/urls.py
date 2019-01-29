from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # path('polls/', include('polls.urls')),  # leaving commented for later reference
    path('admin2/', admin.site.urls)
]
