from django.urls import path
from . import views

app_name = 'nestlist'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>', views.CityView.as_view(), name='city')
]
