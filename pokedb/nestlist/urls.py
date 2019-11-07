from django.urls import path
from . import views

app_name = "nestlist"
urlpatterns = [
    #
    # ~~~~~~~~~~~~~
    # HTML Views
    # ~~~~~~~~~~~~~
    #
    # List of Cities (web-only)
    path("", views.CityIndex.as_view(), name="list_of_cities"),
    # City view
    path(
        "<int:city_id>/",
        views.NestListView.as_view(),
        {"scope": "city", "pk_name": "city_id"},
        name="city",
    ),
    # Nest Details + Hx
    path(
        "<int:city_id>/nest/<int:nest_id>/",
        views.NestHistoryView.as_view(),
        {"scope": "nest", "pk_name": "nest_id", "history": True},
        name="nest_history",
    ),
    # Neighborhood Index
    path(
        "<int:city_id>/neighborhood/",
        views.NeighborhoodIndex.as_view(),
        name="neighborhood_list",
    ),
    # Neighborhood Detail
    path(
        "<int:city_id>/neighborhood/<int:neighborhood_id>/",
        views.NeighborhoodView.as_view(),
        {"scope": "neighborhood", "pk_name": "neighborhood_id"},
        name="neighborhood",
    ),
    # Rotation-specific permalink
    path(
        "<int:city_id>/rotation/<int:date>/",
        views.NestListView.as_view(),
        {"scope": "city", "pk_name": "city_id"},
        name="city_historic_date",
    ),
    # Region index
    path("<int:city_id>/region/", views.RegionalIndex.as_view(), name="region_index"),
    # Region Detail
    path(
        "region/<int:region_id>/",
        views.RegionView.as_view(),
        {"scope": "region", "pk_name": "region_id"},
        name="region",
    ),
    # Park System index
    # path("<int:city_id>/park_sys/", views.ParkSysIndex.as_view(), name="ps_idx"),
    # Park System detail
    path(
        "park_system/<int:ps_id>/",
        views.ParkSystemView.as_view(),
        {"scope": "ps", "pk_name": "ps_id"},
        name="park_sys",
    ),
    # Species history
    path(
        "<int:city_id>/species-history/<str:poke>/",
        views.SpeciesHistoryView.as_view(),
        {
            "scope": "city",
            "pk_name": "city_id",
            "history": True,
            "species_detail": True,
        },
        name="species_history",
    ),
    # Report a nest
    path("<int:city_id>/report/", views.report_nest, name="report_nest"),
    #
    # ~~~~~~~~~~~~~
    # API views
    # ~~~~~~~~~~~~~
    #
    # City overview
    path("<int:city_id>/nests/", views.ParkViewSet.as_view(), name="city_park_list"),
    # Nest detail + history
    path(
        "<int:city_id>/nests/<int:nest_id>/",
        views.NestDetail.as_view(),
        name="nest_detail_view",
    ),
    # Neighborhood Index # TODO
    # path("<int:city_id>/neighborhoods/"),
    # Neighborhood Detail # TODO
    # path("<int:city_id>/neighborhoods/<int:neighborhood_id>/"),
    # region index # TODO
    # path("<int:city_id>/regions/"),
    # region detail # TODO
    # path("regions/<int:region_id>/"),
    # PS index # TODO
    # path("<int:city_id>/park_systems/"),
    # PS detail # TODO
    # path("park_systems/<int:ps_id>/"),
    # Sp Hx # TODO
    # path("<int:city_id>/species/<str:poke>/"),
    # reporting API # TODO
    # path("<int:city_id>/rpt/",),
]
