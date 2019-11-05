from django.urls import path
from . import views

app_name = "nestlist"
urlpatterns = [
    path("", views.CityIndex.as_view(), name="list_of_cities"),
    path(
        "<int:city_id>/",
        views.NestListView.as_view(template_name="nestlist/city.jinja"),
        {"scope": "city", "pk_name": "city_id"},
        name="city",
    ),
    path(
        "<int:city_id>/nest/<int:nest_id>/",
        views.NestListView.as_view(template_name="nestlist/nest.jinja"),
        {"scope": "nest", "pk_name": "nest_id", "history": True},
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
        views.NestListView.as_view(template_name="nestlist/neighborhood.jinja"),
        {"scope": "neighborhood", "pk_name": "neighborhood_id"},
        name="neighborhood",
    ),
    # path("<int:city_id>/neighborhoods/"),
    # path("<int:city_id>/neighborhoods/<int:neighborhood_id>/"),
    path(
        "<int:city_id>/rotation/<int:date>/",
        views.NestListView.as_view(template_name="nestlist/city.jinja"),
        {"scope": "city", "pk_name": "city_id"},
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
    # path("park_system/<int:ps_id>/"),
    path(
        "<int:city_id>/species-history/<str:poke>/",
        views.NestListView.as_view(template_name="nestlist/species-history.jinja"),
        {
            "scope": "city",
            "pk_name": "city_id",
            "history": True,
            "species_detail": True,
        },
        name="species_history",
    ),
    # path("<int:city_id>/species/<str:poke>/"),
    path("<int:city_id>/report/", views.report_nest, name="report_nest"),
]
