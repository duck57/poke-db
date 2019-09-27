from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = "nestlist"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:city_id>;date=<str:date>/", views.CityView.as_view(), name="city_date"),
    path("<int:city_id>/nests/", views.ParkViewSet.as_view(), name="city_park_list"),
    path(
        "<int:city_id>/rotation/<int:date>/",
        views.CityView.as_view(),
        name="city_historic_date",
    ),
    # TODO: rewrite this to use the local reporting form
    path("<int:city_id>/report/", views.report_nest, name="report_nest"),
    path("<int:city_id>/", views.CityView.as_view(), name="city"),
]
