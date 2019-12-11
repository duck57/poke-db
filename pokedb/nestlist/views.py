from typing import Dict, List, Union, Optional, Type

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import QuerySet, Model
from django.shortcuts import render, get_object_or_404
from django.http import (
    HttpResponseRedirect,
    HttpResponseBadRequest,
    Http404,
    HttpResponseNotFound,
    QueryDict,
    HttpResponse,
)
from django.urls import reverse
from urllib.parse import urlencode
from django.views import generic, View
from rest_framework import viewsets
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveAPIView
from drf_multiple_model.views import ObjectMultipleModelAPIView

# Create your views here.
from nestlist.utils import str_int, parse_date, nested_dict, number_format
from speciesinfo.models import (
    Pokemon,
    match_species_by_name_or_number,
    enabled_in_pogo,
    self_as_qs,
)
from .models import (
    NstSpeciesListArchive,
    NstMetropolisMajor,
    NstLocation,
    NstCombinedRegion,
    get_local_nsla_for_rotation,
    NstNeighborhood,
    collect_empty_nests,
    rotations_without_report,
    get_rotation,
    park_nesting_history,
    NstParkSystem,
    species_nesting_history,
    NstRotationDate,
    add_a_report,
    query_nests,
)
from .serializers import (
    ParkSerializer,
    CitySerializer,
    NeighborhoodSerializer,
    ModelTypeSerializer,
    ParkSysSerializer,
    RegionSerializer,
    ReportSerializer,
    ParkDetailSerializer,
)
from .forms import NestReportForm


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
    model_list = {
        "city": NstMetropolisMajor,
        "neighborhood": NstNeighborhood,
        "region": NstCombinedRegion,
        "nest": NstLocation,
        "ps": NstParkSystem,
    }

    def get_raw_date(self) -> str:
        srg = self.request.GET
        return (
            "t"
            if self.kwargs.get("history")
            else self.kwargs.get("date", srg.get("date", srg.get("rotation", "t")))
        )

    def get_parsed_date(self):
        return parse_date(str(self.get_raw_date()))

    def get_rot8(self) -> NstRotationDate:
        return get_rotation(self.get_raw_date())

    def get_sp(self) -> Union[int, str]:
        srg = self.request.GET
        return self.kwargs.get(
            "poke", srg.get("pokemon", srg.get("species", srg.get("pokémon", None)))
        )

    def get_pk(self):
        return self.kwargs[self.kwargs["pk_name"]]

    def eligible_parks(self) -> "QuerySet[NstLocation]":
        return query_nests("", self.get_pk(), self.kwargs["pk_name"])

    def get_scope(self) -> Optional[str]:
        return self.kwargs.get("scope")

    def plural_scope(self) -> str:
        return {
            "neighborhood": "neighborhoods",
            "city": "cities",
            "region": "regions",
            "ps": "park systems",
            "nest": "parks",
        }.get(self.get_scope(), "mysteries")

    def get_location(self):
        try:
            return self.model_list[self.get_scope()].objects.get(pk=self.get_pk())
        except ObjectDoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        scope: str = self.get_scope()
        pk = self.get_pk()
        location = self.get_location()
        ss: str = self.get_sp()
        if not location:
            return HttpResponseNotFound(f"No {scope} with id {pk}")
        if (
            scope in ["neighborhood", "nest"]
            and location.ct().pk != self.kwargs["city_id"]
        ):  # always correct URLs for Neighborhoods & Nests
            return HttpResponseRedirect(
                append_search_terms(location.web_url(), self.request.GET)
            )
        try:
            return super(NestListMixin, self).get(request, *args, **kwargs)
        except ValueError:
            return HttpResponseBadRequest(f"Try again with a valid date.")
        except Http404:
            err_str: str = f"🚫 No nests found for {scope} #{pk}"
            if scope != "nest":
                err_str += f" on {self.get_rot8()}"
            if ss:
                err_str += f" matching a search for {ss}"
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
        scope = self.get_scope()
        pk = self.get_pk()
        species = self.get_sp()
        if self.kwargs.get("species_detail"):
            return species_nesting_history(sp=species, city=self.eligible_parks())
        if scope in ["neighborhood", "city", "ps", "region"]:
            return get_local_nsla_for_rotation(
                rotation=self.get_rot8(),
                location_pk=pk,
                location_type=scope,
                species=species,
            )
        elif scope == "nest":
            return park_nesting_history(nest=pk, species=species)
        else:  # error
            return NstSpeciesListArchive.objects.none()

    def get_context_data(self, **kwargs) -> Dict:
        """
        :return: context data for the templates
        """
        context: Dict = super().get_context_data(**kwargs)
        loc = self.get_location()
        context["location"] = loc
        context["rotation"]: NstRotationDate = self.get_rot8()
        context["raw_date"]: str = self.get_raw_date()
        context["parsed_date"]: str = self.get_parsed_date()
        context["history"]: bool = True if self.kwargs.get("history") else False
        context["pk"] = self.get_pk()
        # these may be removed for performance later
        context["cities_touched"] = loc.city_list()
        context["regions_touched"] = loc.region_list()
        context["neighborhoods"] = loc.neighborhood_list()
        context["all_parks"] = loc.park_list()
        context["ps_touched"] = loc.park_system_list()
        try:
            context["species_search"]: Pokemon = (
                match_species_by_name_or_number(
                    sp_txt=self.get_sp(),
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
        ) else self.get_sp()
        context["scope"] = self.get_scope()
        context["scope_plural"] = self.plural_scope()
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
            self.get_pk(), str(self.get_sp())
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
        sp: str = self.get_sp()
        context["species_links"]: "QuerySet[Pokemon]" = (
            Pokemon.objects.filter(
                nstspecieslistarchive__in=species_nesting_history(
                    sp=sp, city=self.eligible_parks()
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
    serializers = {
        NstMetropolisMajor: CitySerializer,
        NstNeighborhood: NeighborhoodSerializer,
        NstLocation: ParkDetailSerializer,
        NstParkSystem: ParkSysSerializer,
        NstCombinedRegion: RegionSerializer,
    }

    def get_querylist(self):
        loc = self.get_location()

        querylist = [
            {
                "label": "self",
                "queryset": self_as_qs(loc),
                "serializer_class": self.serializers[type(loc)],
            },
            {
                "label": "type",
                "queryset": self_as_qs(loc),
                "serializer_class": ModelTypeSerializer,
            },
            {
                "label": "city",
                "queryset": self_as_qs(loc.ct()),
                "serializer_class": CitySerializer,
            },
            {
                "label": "neighborhoods",
                "queryset": loc.neighborhood_list(),
                "serializer_class": NeighborhoodSerializer,
            },
            {
                "label": "park systems",
                "queryset": loc.park_system_list(),
                "serializer_class": ParkSysSerializer,
            },
            {
                "label": "regions",
                "queryset": loc.region_list(),
                "serializer_class": RegionSerializer,
            },
            {
                "label": "current list",
                "queryset": get_local_nsla_for_rotation(
                    self.get_rot8(), location_pk=loc, species=self.get_sp()
                ),
                "serializer_class": ReportSerializer,
            },
        ]
        if type(loc) in [NstNeighborhood, NstParkSystem] and not self.get_sp():
            querylist.append(
                {
                    "label": "empties",
                    "queryset": collect_empty_nests(
                        location_pk=loc, rotation=self.get_rot8()
                    ),
                    "serializer_class": ParkSerializer,
                }
            )
        return querylist

    def get_queryset(self):
        return self_as_qs(self.get_location().ct())


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


class NestDetail(RetrieveAPIView):
    model = NstLocation
    serializer_class = ParkSerializer
    pass
