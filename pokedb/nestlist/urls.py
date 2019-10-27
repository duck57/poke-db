from django.urls import path
from . import views

app_name = "nestlist"
urlpatterns = [
    path("", views.CityIndex.as_view(), name="list_of_cities"),
    path("<int:city_id>/", views.CityView.as_view(), name="city"),
    path(
        "<int:city_id>/nest/<int:nest_id>/",
        views.NestView.as_view(),
        name="nest_history",
    ),
    path("<int:city_id>/nests/", views.ParkViewSet.as_view(), name="city_park_list"),
    path(
        "<int:city_id>/nests/<int:nest_id>/",
        views.NestDetail.as_view(),
        name="nest_detail_view",
    ),
    path(
        "<int:city_id>/neighborhood/",
        views.NeighborhoodIndex.as_view(),
        name="neighborhood_list",
    ),
    path(
        "<int:city_id>/neighborhood/<int:neighborhood_id>/",
        views.NeighborhoodView.as_view(),
        name="neighborhood",
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
    path("<int:city_id>/region/", views.RegionalIndex.as_view(), name="region_index"),
    # path(  # region HTML views
    #     "region/<int:region_id>/", views.RegionView.as_view(), name="region"
    # ),  # TODO: region views
    # path("<int:city_id>/regions/"),  # region API index
    # path("regions/<int:region_id>/"),  # region API detail
    # TODO: park systems
    # path("<int:city_id>/park_sys/", views.ParkSysIndex.as_view(), name="ps_idx"),
    # path(
    #     "region/<int:ps_id>/", views.ParkSystemView.as_view(), name="park_sys"
    # ),
    # path("<int:city_id>/park_systems/"),
    # path("park_system/<int:region_id>/"),
    # path("<int:city_id>/species-history/<str:poke>/"),
    # path("<int:city_id>/species/<str:poke>/"),
    # TODO: rewrite this to use the local reporting form
    path("<int:city_id>/report/", views.report_nest, name="report_nest"),
]
