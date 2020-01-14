from urllib.parse import urlencode

from django.core.exceptions import MultipleObjectsReturned
from django.db.models import Model, Value, IntegerField, CharField, BooleanField
from django.http import HttpResponseBadRequest, Http404, HttpResponseNotFound, QueryDict
from django.shortcuts import render
from django.views import generic, View
from drf_multiple_model.views import ObjectMultipleModelAPIView
from rest_framework.permissions import IsAuthenticated

# Create your views here.
from nestlist.utils import number_format
from .forms import NestReportForm
from .models import *
from .serializers import *

"""
Stand-alone methods
"""


def append_search_terms(url_base: str, terms: QueryDict):
    """This might be redundant with some core Django functionality"""
    return url_base + "?" + urlencode(terms) if terms else url_base


def report_nest(request, **kwargs):
    try:
        city = NstMetropolisMajor.objects.get(pk=kwargs["city_id"], active=True)
    except ObjectDoesNotExist:
        return Http404(f"{kwargs['city_id']} is not a valid city")
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = NestReportForm(request.POST, city=city)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            cd = form.cleaned_data
            submission_status = add_a_report(
                name=cd["your_name"].lower().strip(),
                bot_id=city.airtable_bot.pk if city.airtable_bot else None,
                nest=cd["park"].strip(),
                species=cd["species"].strip(),
                timestamp=parse_date(str(cd["timestamp"])),
                server="🕸",
                subsearch_place=cd["subplace"],
                subsearch_type=cd["scope"],
            )

            # thank-you page
            return render(
                request,
                "nestlist/thankyou.jinja",
                {
                    "location": city,
                    "status": submission_status.status,
                    "errors": submission_status.errors_by_location,
                },
            )

    # if a GET (or any other method) we'll create a blank form
    else:
        form = NestReportForm()

    return render(
        request, "nestlist/report-form.jinja", {"form": form, "location": city}
    )


"""
Mixins
"""


class NestListMixin(View):
    model_list: "Dict[str, Tuple[Place, str]]" = {
        "city": (NstMetropolisMajor, "city_id"),
        "neighborhood": (NstNeighborhood, "neighborhood_id"),
        "region": (NstCombinedRegion, "region_id"),
        "nest": (NstLocation, "nest_id"),
        "ps": (NstParkSystem, "ps_id"),
    }
    scope_names: "Dict[Type[Place], Tuple[str, str]]" = {
        NstMetropolisMajor: ("city", "city_id"),
        NstNeighborhood: ("neighborhood", "neighborhood_id"),
        NstCombinedRegion: ("region", "region_id"),
        NstLocation: ("nest", "nest_id"),
        NstParkSystem: ("ps", "ps_id"),
    }

    @property
    def raw_date(self) -> str:
        srg = self.request.GET
        return (
            "t"
            if self.kwargs.get("history")
            else self.kwargs.get("date", srg.get("date", srg.get("rotation", "t")))
        )

    @property
    def parsed_date(self):
        return parse_date(self.raw_date)

    @property
    def rot8(self) -> NstRotationDate:
        return get_rotation(self.raw_date)

    @property
    def species_search(self) -> Optional[Union[int, str]]:
        srg = self.request.GET
        return self.kwargs.get(
            "poke", srg.get("pokemon", srg.get("species", srg.get("pokémon", None)))
        )

    @property
    def loc_pk(self):
        return self.kwargs[self.kwargs["pk_name"]]

    def eligible_parks(self) -> "QuerySet[NstLocation]":
        return query_nests("", self.loc_pk, self.kwargs["pk_name"])

    @property
    def scope(self) -> str:
        return self.kwargs.get("scope", "unknown")

    @property
    def plural_scope(self) -> str:
        return {
            "neighborhood": "neighborhoods",
            "city": "cities",
            "region": "regions",
            "ps": "park systems",
            "nest": "parks",
        }.get(self.scope, "mysteries")

    @property
    def location(self):
        try:
            return self.model_list[self.scope][0].objects.get(pk=self.loc_pk)
        except ObjectDoesNotExist:
            return None

    @location.setter
    def location(self, place: Place):
        self.kwargs["pk_name"] = self.scope_names.get(type(place), "")[1]
        self.kwargs["scope"] = self.scope_names.get(type(place), "")[0]
        self.kwargs[self.kwargs["pk_name"]] = place.pk

    def get(self, request, *args, **kwargs):
        if not self.location:
            return HttpResponseNotFound(f"No {self.scope} with id {self.loc_pk}")
        try:
            return super(NestListMixin, self).get(request, *args, **kwargs)
        except ValueError:
            return HttpResponseBadRequest(f"Try again with a valid date.")
        except Http404:
            err_str: str = f"🚫 No nests found for {self.scope} #{self.loc_pk}"
            if self.scope != "nest":
                err_str += f" on {self.rot8}"
            if self.species_search:
                err_str += f" matching a search for {self.species_search}"
            err_str += f"."
            return HttpResponseNotFound(err_str)


"""
CBVs for the HTML display
"""


class NestListView(generic.ListView, NestListMixin):
    model = NstSpeciesListArchive
    context_object_name = "current_nest_list"
    allow_empty = True
    template_name = "nestlist/city.jinja"

    def get_queryset(self) -> "QuerySet[NstSpeciesListArchive]":
        """
        Unified method for generating a the Nest List
        :return: the NSLA Q set
        """
        if self.kwargs.get("species_detail"):
            return species_nesting_history(
                sp=self.species_search, city=self.eligible_parks()
            )
        if self.scope in ["neighborhood", "city", "ps", "region"]:
            return get_local_nsla_for_rotation(
                rotation=self.rot8,
                location_pk=self.loc_pk,
                location_type=self.scope,
                species=self.species_search,
            )
        elif self.scope == "nest":
            return park_nesting_history(nest=self.loc_pk, species=self.species_search)
        else:  # error
            return NstSpeciesListArchive.objects.none()

    def get_context_data(self, **kwargs) -> Dict:
        """
        :return: context data for the templates
        """
        context: Dict = super().get_context_data(**kwargs)
        context["location"] = self.location
        context["rotation"]: NstRotationDate = self.rot8
        context["raw_date"]: str = self.raw_date
        context["parsed_date"]: str = self.parsed_date
        context["history"]: bool = True if self.kwargs.get("history") else False
        context["pk"] = self.loc_pk
        # these may be removed for performance later
        context["cities_touched"] = self.location.city_list()
        context["regions_touched"] = self.location.region_list()
        context["neighborhoods"] = self.location.neighborhood_list()
        context["all_parks"] = self.location.park_list()
        context["ps_touched"] = self.location.park_system_list()
        try:
            context["species_search"]: Pokemon = (
                match_species_by_name_or_number(
                    sp_txt=self.species_search,
                    age_up=True,
                    previous_evolution_search=True,
                    only_one=True,
                    input_set=enabled_in_pogo(
                        Pokemon.objects.all()
                    ),  # prevent MultipleObjectsReturned
                )
                .exclude(pk="(Egg)")  # keeps things working smoothly (eggs don't nest)
                .get()
            )
        except ObjectDoesNotExist:
            pass
        except MultipleObjectsReturned:
            pass
        context["species_name"]: str = context["species_search"].name if context.get(
            "species_search"
        ) else self.species_search
        context["scope"] = self.scope
        context["scope_plural"] = self.plural_scope
        context["number_format"] = number_format
        context["nearby_radius"] = self.kwargs.get("radius", 0)
        return context


class NeighborhoodView(NestListView):
    template_name = "nestlist/neighborhood.jinja"

    def get_context_data(self, **kwargs) -> Dict:
        context = super().get_context_data(**kwargs)
        context["neighbor_view"]: bool = True
        context["empties"]: "QuerySet[NstLocation]" = collect_empty_nests(
            rotation=context["rotation"], location_pk=context["location"]
        )
        return context


class NestHistoryView(NestListView):
    template_name = "nestlist/nest.jinja"

    def get_context_data(self, **kwargs) -> Dict:
        context = super().get_context_data(**kwargs)
        nest: NstLocation = context["location"]
        context["nest_view"]: bool = True
        context["other_names"]: List[str] = [nest.short_name] if nest.short_name else []
        for name in nest.alternate_name.exclude(hide_me=True):
            context["other_names"].append(name.name)
        context["empty_rotations"] = rotations_without_report(
            self.loc_pk, self.species_search
        )
        context["current_nest"] = NstSpeciesListArchive.objects.filter(
            nestid=context["location"], rotation_num=context["rotation"]
        )
        context["scope_plural"] = "nests"
        return context


class SpeciesHistoryView(NestListView):
    template_name = "nestlist/species-history.jinja"

    def get_context_data(self, **kwargs) -> Dict:
        context: Dict = super().get_context_data(**kwargs)
        context["species_links"]: "QuerySet[Pokemon]" = (
            Pokemon.objects.filter(
                nstspecieslistarchive__in=species_nesting_history(
                    sp=self.species_search, city=self.eligible_parks()
                )
            ).distinct()
        )
        context["species_count"]: int = (context["species_links"].count())
        return context


class RegionView(NestListView):
    template_name = "nestlist/region.jinja"

    def get_context_data(self, **kwargs) -> Dict:
        context: Dict = super().get_context_data(**kwargs)
        context["cities_touched"]: Dict = nested_dict()
        for n in context["neighborhoods"].order_by("name"):
            context["cities_touched"][n.major_city][n] = n
        return context


class ParkSystemView(RegionView):
    template_name = "nestlist/park-sys.jinja"

    def get_context_data(self, **kwargs) -> Dict:
        context: Dict = super().get_context_data(**kwargs)
        context["cities_touched"]: Dict = nested_dict()
        for p in context["all_parks"].order_by("official_name"):
            context["cities_touched"][p.ct()][p] = p
        return context


"""
Index Views
"""


class NeighborhoodIndex(generic.ListView):
    model = NstNeighborhood
    context_object_name = "place_list"
    template_name = "nestlist/neighborhood_index.jinja"

    def get_queryset(self):
        return NstNeighborhood.objects.filter(
            major_city=self.kwargs["city_id"]
        ).order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["scope_name"] = "neighborhood"
        context["scope_plural"] = "neighborhoods"
        context["parent_city"] = NstMetropolisMajor.objects.get(
            pk=self.kwargs["city_id"]
        )
        context["title"] = f"Neighborhoods & Suburbs of {context['parent_city'].name}"
        return context


class RegionalIndex(generic.ListView):
    model = NstNeighborhood
    context_object_name = "place_list"
    template_name = "nestlist/region_index.jinja"

    def get_queryset(self):
        return (
            NstCombinedRegion.objects.filter(
                nstneighborhood__major_city=self.kwargs["city_id"]
            )
            .distinct()
            .order_by("name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["scope_name"] = "region"
        context["scope_plural"] = "regions"
        context["parent_city"] = NstMetropolisMajor.objects.get(
            pk=self.kwargs["city_id"]
        )
        context["title"] = f"Regions of {context['parent_city'].name}"
        return context


class CityIndex(generic.ListView):
    model = NstMetropolisMajor
    template_name = "nestlist/city_index.jinja"
    context_object_name = "place_list"

    def get_queryset(self):
        return NstMetropolisMajor.objects.filter(active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["scope_name"] = "city"
        context["scope_plural"] = "cities"
        context["title"] = "Cities reporting to this server"
        return context


"""
API views
"""


class NestListAPI(ObjectMultipleModelAPIView, NestListMixin):
    def get_querylist(
        self,
        *,
        list_parts: bool = False,
        self_serializer: "Type[serializers.Serializer]" = ParkDetailSerializer,
        hide_neighborhood: bool = False,
        hide_ps: bool = False,
    ):

        queries: Dict[str, Dict[str]] = {
            "city": {
                "label": "city",
                "queryset": self.location.city_list(),
                "serializer_class": CitySerializer,
            },
            "neighborhood": {
                "label": "neighborhoods",
                "queryset": self.location.neighborhood_list(),
                "serializer_class": NeighborhoodSerializer,
            },
            "park system": {
                "label": "park systems",
                "queryset": self.location.park_system_list(),
                "serializer_class": ParkSysSerializer,
            },
            "region": {
                "label": "regions",
                "queryset": self.location.region_list(),
                "serializer_class": RegionSerializer,
            },
            "nestlist": {
                "label": "current list",
                "queryset": self.location.park_list()
                .filter(
                    nstspecieslistarchive__in=get_local_nsla_for_rotation(
                        self.rot8, self.location, species=self.species_search
                    )
                )
                .annotate(rot=Value(self.rot8.pk, output_field=IntegerField()))
                .annotate(
                    hide_neighborhood=Value(
                        hide_neighborhood, output_field=BooleanField()
                    )
                )
                .annotate(hide_ps=Value(hide_ps, output_field=BooleanField())),
                "serializer_class": ParkSerializer,
            },
            "empties": {
                "label": "empties",
                "queryset": collect_empty_nests(
                    location_pk=self.location, rotation=self.rot8
                )
                .annotate(
                    hide_neighborhood=Value(
                        hide_neighborhood, output_field=BooleanField()
                    )
                )
                .annotate(hide_ps=Value(hide_ps, output_field=BooleanField()))
                .annotate(hide_sp=Value(True, output_field=BooleanField())),
                "serializer_class": ParkSerializer,
            },
            "all parks": {
                "label": "all parks",
                "queryset": self.location.park_list()
                .annotate(
                    hide_neighborhood=Value(
                        hide_neighborhood, output_field=BooleanField()
                    )
                )
                .annotate(hide_ps=Value(hide_ps, output_field=BooleanField())),
                "serializer_class": ParkSerializer,
            },
        }

        querylist = [
            {
                "label": "self",
                "queryset": self_as_qs(self.location),
                "serializer_class": self_serializer,
            },
            {
                "label": "rotation",
                "queryset": self_as_qs(self.rot8),
                "serializer_class": RotationSerializer,
            },
            {
                "label": "type",
                "queryset": self_as_qs(self.location),
                "serializer_class": ModelTypeSerializer,
            },
        ]

        if self.species_search or self.species_search == 0:
            querylist.append(
                {
                    "label": "species restriction",
                    "queryset": self_as_qs(self.location).annotate(
                        str=Value(str(self.species_search), output_field=CharField())
                    ),
                    "serializer_class": StringSerializer,
                }
            )

        return (querylist, queries) if list_parts else querylist

    def get_queryset(self):
        return self_as_qs(None)


class CityAPI(NestListAPI):
    def get_querylist(self):
        querylist, parts = super().get_querylist(
            list_parts=True, self_serializer=CitySerializer
        )
        querylist.extend(
            [
                parts["nestlist"],
                parts["neighborhood"],
                parts["park system"],
                parts["region"],
            ]
        )
        return querylist


class NestDetailAPI(NestListAPI):
    def get_querylist(self):
        return super().get_querylist(self_serializer=ParkDetailSerializer)


class NeighborhoodAPI(NestListAPI):
    def get_querylist(self):
        querylist, parts = super().get_querylist(
            list_parts=True, self_serializer=CitySerializer, hide_neighborhood=True
        )
        querylist.extend([parts["city"], parts["region"], parts["nestlist"]])
        if self.species_search != 0 and not self.species_search:
            querylist.append(parts["empties"])
        querylist.append(parts["park system"])
        return querylist


class RegionalAPI(NestListAPI):
    def get_querylist(self):
        querylist, parts = super().get_querylist(
            list_parts=True, self_serializer=RegionSerializer
        )
        querylist.extend(
            [
                parts["neighborhood"],
                parts["city"],
                parts["nestlist"],
                parts["park system"],
            ]
        )
        return querylist


class PsAPI(NestListAPI):
    def get_querylist(self):
        querylist, parts = super().get_querylist(
            list_parts=True, self_serializer=ParkSysSerializer, hide_ps=True
        )
        querylist.append(
            parts["all parks"]
            if self.species_search != 0 and not self.species_search
            else parts["nestlist"]
        )
        querylist.extend([parts["city"], parts["region"], parts["neighborhood"]])
        return querylist


class LocationSearchAPI(ObjectMultipleModelAPIView):
    def distance_search(self, model: Type[Model], radius: float) -> QuerySet:
        at: float = self.kwargs["lat"]
        on: float = self.kwargs["lon"]
        return model.objects.within_y_km(at, on, radius)

    def get_querylist(self):
        querylist = [
            {
                "label": "nests",
                "queryset": self.distance_search(NstLocation, 5),  # 3 mi radius
                "serializer_class": ParkSerializer,
            },
            {
                "label": "cities",
                "queryset": self.distance_search(
                    NstMetropolisMajor, 256
                ),  # 159 mi radius
                "serializer_class": CitySerializer,
            },
            {
                "label": "neighborhoods",
                "queryset": self.distance_search(
                    NstNeighborhood, 18.86
                ),  # 11.7 mi radius
                "serializer_class": NeighborhoodSerializer,
            },
        ]
        return querylist

    def get_queryset(self) -> QuerySet:
        return self_as_qs(None)


class CityAuthMixin(NestListMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            self.location = request.user.nest_user.city
        except AttributeError:
            return HttpResponseNotFound  # improperly configured user
        return super().get(request, args, kwargs)


class LocalCity(CityAuthMixin, CityAPI):
    """
    CityAPI but with an auth token indirectly providing the city ID instead of the URL
    """
