from django.urls import path, re_path
from . import views

app_name = "nestlist"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:city_id>/", views.CityView.as_view(), name="city_date"),
    path(
        "<int:city_id>/nest/<int:nest_id>/",
        views.NestView.as_view(),
        name="nest_history",
    ),
    path("<int:city_id>/nests/", views.ParkViewSet.as_view(), name="city_park_list"),
    # path("<int:city_id>/nests/empties/"),
    # path("<int:city_id>/nests/confirmed/"),
    # path("<int:city_id>/nests/unconfirmed/"),
    # path("<int:city_id>/nests/<int:nest_id>/", views."),
    # path("<int:city_id>/neighborhood/")
    path(
        "<int:city_id>/neighborhood/<int:neighborhood_id>/",
        views.CityView.as_view(),
        name="neighborhood_view",
    ),
    # path("<int:city_id>/neighborhoods/"),
    # path("<int:city_id>/neighborhoods/<int:neighborhood_id>/"),
    path(
        "<int:city_id>/rotation/<int:date>/",
        views.CityView.as_view(),
        name="city_historic_date",
    ),
    # path(
    #     "<int:city_id>/rotation/<int:date>/",
    #     views.CityView.as_view(),
    #     name="city_historic_date",
    # ),
    # path("<int:city_id>/region/", ),
    path(
        "<int:city_id>/region/<int:region_id>/",
        views.CityView.as_view(),
        name="region_view",
    ),
    # path("<int:city_id>/regions/"),
    # path("<int:city_id>/regions/<int:region_id>/"),
    # path("<int:city_id>/species-history/<str:poke>/"),
    # path("<int:city_id>/species/<str:poke>/"),
    # TODO: rewrite this to use the local reporting form
    path("<int:city_id>/report/", views.report_nest, name="report_nest"),
]
