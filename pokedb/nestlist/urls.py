from django.urls import path, register_converter
from . import converters, views

register_converter(converters.FloatConverter, "float")

app_name = "nestlist"
urlpatterns = [
    #
    # ~~~~~~~~~~~~~
    # HTML Views
    # ~~~~~~~~~~~~~
    #
    # List of Cities (web-only)
    # path("", views.CityIndex.as_view(), name="list_of_cities"),
    # City view
    path(
        "city/<int:city_id>/",
        views.NestListView.as_view(),
        # 288 km ≈ 180 miles, a dedicated day trip
        {"scope": "city", "pk_name": "city_id", "radius": 288},
        name="city",
    ),
    # Nest Details + Hx
    path(
        "nest/<int:nest_id>/",
        views.NestHistoryView.as_view(),
        # 1.6 km chosen as a reasonable easy walking distance
        {"scope": "nest", "pk_name": "nest_id", "history": True, "radius": 1.6},
        name="nest_history",
    ),
    # Neighborhood Index
    path(
        "city/<int:city_id>/neighborhoods/",
        views.NeighborhoodIndex.as_view(),
        name="neighborhood_list",
    ),  # only kept because it's already here
    # Neighborhood Detail
    path(
        "neighborhood/<int:neighborhood_id>/",
        views.NeighborhoodView.as_view(),
        # 12.34 km ≈ 7.7 miles (a quick drive)
        {"scope": "neighborhood", "pk_name": "neighborhood_id", "radius": 12.34},
        name="neighborhood",
    ),
    # Rotation-specific permalink
    path(
        "city/<int:city_id>/rotation/<int:date>/",
        views.NestListView.as_view(),
        {"scope": "city", "pk_name": "city_id"},
        name="city_historic_date",
    ),
    # Region index  # only kept because it's already here
    path(
        "city/<int:city_id>/regions/",
        views.RegionalIndex.as_view(),
        name="region_index",
    ),
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
        "park-system/<int:ps_id>/",
        views.ParkSystemView.as_view(),
        {"scope": "ps", "pk_name": "ps_id"},
        name="park_sys",
    ),
    # Species history
    path(
        "city/<int:city_id>/species-history/<str:poke>/",
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
    path("report/<int:city_id>/", views.report_nest, name="report_nest"),
    #
    # ~~~~~~~~~~~~~
    # API views
    # ~~~~~~~~~~~~~
    #
    # City overview
    path(
        "cities/<int:city_id>/",
        views.CityAPI.as_view(),
        {"scope": "city", "pk_name": "city_id"},
        name="city_api_view",
    ),
    # Nest detail + history
    path(
        "nests/<int:nest_id>/",
        views.NestDetailAPI.as_view(),
        {"scope": "nest", "pk_name": "nest_id"},
        name="nest_api_detail",
    ),
    # Neighborhood Index  # not necessary
    # path("<int:city_id>/neighborhoods/"),
    # Neighborhood Detail
    path(
        "neighborhoods/<int:neighborhood_id>/",
        views.NeighborhoodAPI.as_view(),
        {"scope": "neighborhood", "pk_name": "neighborhood_id"},
        name="neighborhood_api",
    ),
    # region index  # not necessary
    # path("<int:city_id>/regions/"),
    # region detail
    path(
        "regions/<int:region_id>/",
        views.RegionalAPI.as_view(),
        {"scope": "region", "pk_name": "region_id"},
        name="region_api",
    ),
    # PS index  # not necessary
    # path("<int:city_id>/park_systems/"),
    # PS detail
    path(
        "park-systems/<int:ps_id>/",
        views.PsAPI.as_view(),
        {"scope": "ps", "pk_name": "ps_id"},
        name="ps_api",
    ),
    # Search by GPS coordinates
    path(
        "nearby/lat=<float:lat>;lon=<float:lon>/",
        views.LocationSearchAPI.as_view(),
        name="location_search",
    ),
    # Sp Hx API # TODO
    # path("cities/<int:city_id>/species-history/<str:poke>/",
    # views.SpHxAPI.as_view(), name="species_history"),
    # reporting API # TODO
    # path("report-api_1/", views.report_API(), name="report_api"),
]
