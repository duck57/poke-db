from typing import Dict

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from django.shortcuts import render, get_object_or_404
from django.http import (
    HttpResponseRedirect,
    HttpResponseBadRequest,
    Http404,
    HttpResponseNotFound,
    QueryDict,
)
from django.urls import reverse
from urllib.parse import urlencode
from django.views import generic
from rest_framework import viewsets
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveAPIView

# Create your views here.
from nestlist.utils import str_int
from speciesinfo.models import Pokemon, match_species_by_name_or_number, enabled_in_pogo
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
)
from .serializers import ParkSerializer


def append_search_terms(url_base: str, terms: QueryDict):
    """This might be redundant with some core Django functionality"""
    return url_base + "?" + urlencode(terms) if terms else url_base


def report_nest(request, **kwargs):
    """
    TODO: replace this with real class-based methods
    This is a placeholder until further dev work finishes to
    allow this to take precedence
    :param request:
    :param kwargs:
    :return:
    """
    return HttpResponseRedirect("http://columbusnestreport.cf")


class NestListView(generic.ListView):
    model = NstSpeciesListArchive
    context_object_name = "current_nest_list"
    allow_empty = False
    model_list = {
        "city": NstMetropolisMajor,
        "neighborhood": NstNeighborhood,
        "region": NstCombinedRegion,
        "nest": NstLocation,
        "ps": NstParkSystem,
    }

    def get_rot8(self):
        srg = self.request.GET
        return get_rotation(
            self.kwargs.get("date", srg.get("date", srg.get("rotation", "t")))
        )

    def get_sp(self):
        srg = self.request.GET
        return srg.get("pokemon", srg.get("species", srg.get("pokémon", None)))

    def get_queryset(self) -> "QuerySet[NstSpeciesListArchive]":
        scope = self.kwargs["scope"]
        pk = self.kwargs[self.kwargs["pk_name"]]
        species = self.get_sp()
        if self.kwargs.get("species_detail"):
            return species_nesting_history(sp=self.kwargs["poke"], city=pk)
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

    def get(self, request, *args, **kwargs):
        scope = self.kwargs["scope"]
        pk = self.kwargs[self.kwargs["pk_name"]]
        try:
            location = self.model_list[scope].objects.get(pk=pk)
        except ObjectDoesNotExist:
            return HttpResponseNotFound(f"No {scope} with id {pk}")
        if (
            scope in ["neighborhood", "nest"]
            and location.ct().pk != self.kwargs["city_id"]
        ):  # always correct URLs for Neighborhoods & Nest
            return HttpResponseRedirect(
                append_search_terms(location.web_url(), self.request.GET)
            )
        try:
            return super(NestListView, self).get(request, *args, **kwargs)
        except ValueError:
            return HttpResponseBadRequest(f"Try again with a valid date.")
        except Http404:
            errstring = f"No nests found for {scope} #{pk}"
            if scope != "nest":
                errstring += f" on {self.get_rot8()}"
            ss = self.get_sp()
            if ss:
                errstring += f" matching a search for {ss}"
            errstring += f"."
            return HttpResponseNotFound(errstring)

    def get_context_data(self, **kwargs) -> Dict:
        context = super().get_context_data(**kwargs)
        scope = self.kwargs["scope"]
        pk = self.kwargs[self.kwargs["pk_name"]]
        context["location"] = self.model_list[scope].objects.get(pk=pk)
        context["rotation"] = self.get_rot8()
        if scope == "neighborhood":
            context["neighbor_view"] = True
            context["empties"] = collect_empty_nests(
                rotation=context["rotation"],
                location_type="neighborhood",
                location_pk=pk,
            )
        elif scope == "nest":
            context["nest_view"] = True
        if self.kwargs.get("history"):
            context["history"] = True
            if self.kwargs.get("species_detail"):
                sp = self.kwargs["poke"]
                context["species_count"] = (
                    species_nesting_history(sp=sp, city=pk)
                    .values("species_name_fk")
                    .distinct()
                    .count()
                )
                context["species_name"] = (
                    match_species_by_name_or_number(
                        sp_txt=sp,
                        age_up=True,
                        previous_evolution_search=True,
                        only_one=True,
                        input_set=enabled_in_pogo(
                            Pokemon.objects.all()
                        ),  # prevent MultipleObjectsReturned
                    )
                    .exclude(
                        pk="(Egg)"
                    )  # keeps things working smoothly (eggs don't nest)
                    .get()
                    .name
                    if str_int(sp)
                    else sp
                )
        return context


class NeighborhoodIndex(generic.ListView):
    model = NstNeighborhood
    context_object_name = "place_list"
    template_name = "nestlist/neighborhood_index.html"

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
    template_name = "nestlist/region_index.html"

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
    template_name = "nestlist/city_index.html"
    context_object_name = "place_list"

    def get_queryset(self):
        return NstMetropolisMajor.objects.filter(active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["scope_name"] = "city"
        context["scope_plural"] = "cities"
        return context


class ParkViewSet(ListAPIView):
    model = NstLocation
    serializer_class = ParkSerializer

    def get_queryset(self):
        return NstLocation.objects.filter(neighborhood=self.kwargs["city_id"])


class NestDetail(RetrieveAPIView):
    pass
