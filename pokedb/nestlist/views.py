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
from .models import (
    NstSpeciesListArchive,
    NstMetropolisMajor,
    NstLocation,
    NstCombinedRegion,
    get_local_nsla_for_rotation,
    NstNeighborhood,
    collect_empty_nests,
    get_rotation,
)
from .serializers import ParkSerializer


def append_search_terms(url_base: str, terms: QueryDict):
    """This might be redundant with some core Django functionality"""
    return url_base + "?" + urlencode(terms)


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


class CityView(generic.ListView):
    model = NstSpeciesListArchive
    template_name = "nestlist/city.html"
    context_object_name = "current_nest_list"
    pk_url_kwarg = "city_id"
    allow_empty = False

    def get_queryset(self):
        srg = self.request.GET
        return get_local_nsla_for_rotation(
            get_rotation(srg.get("date", "t")),
            self.kwargs["city_id"],
            "city",
            species=srg.get("pokemon", srg.get("species", srg.get("pokémon", None))),
        )

    def get(self, request, *args, **kwargs):
        try:
            return super(CityView, self).get(request, *args, **kwargs)
        except ValueError:
            return HttpResponseBadRequest(f"Try again with a valid date.")
        except Http404:
            srg = self.request.GET
            errstring = f"No nests found for city #{self.kwargs['city_id']} "
            errstring += f"on {srg.get('date', srg.get('rotation', 'today'))}"
            ss = srg.get("pokemon", srg.get("species", srg.get("pokémon", None)))
            if ss:
                errstring += f" matching a search for {ss}"
            errstring += f"."
            return HttpResponseNotFound(errstring)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["location"] = NstMetropolisMajor.objects.get(pk=self.kwargs["city_id"])
        context["rotation"] = get_rotation(self.kwargs.get("date", "t"))
        # context["title"] = "List of Nest Databases"
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


class NestView(generic.DetailView):
    model = NstLocation
    template_name = "nestlist/nest.html"


class NeighborhoodView(generic.ListView):
    model = NstSpeciesListArchive
    template_name = "nestlist/neighborhood.html"
    context_object_name = "current_nest_list"
    pk_url_kwarg = "neighborhood_id"
    allow_empty = False

    def get_queryset(self):
        srg = self.request.GET
        return get_local_nsla_for_rotation(
            get_rotation(srg.get("date", "t")),
            self.kwargs["neighborhood_id"],
            "neighborhood",
            species=srg.get("pokemon", srg.get("species", srg.get("pokémon", None))),
        )

    def get(self, request, *args, **kwargs):
        nid: int = self.kwargs["neighborhood_id"]
        try:
            nbd: NstNeighborhood = NstNeighborhood.objects.get(pk=nid)
        except NstNeighborhood.DoesNotExist:
            return HttpResponseNotFound(f"No neighborhood or suburb with id {nid}")
        if nbd.major_city.pk != self.kwargs["city_id"]:
            return HttpResponseRedirect(
                append_search_terms(nbd.web_url(), self.request.GET)
            )
        try:
            return super(NeighborhoodView, self).get(request, *args, **kwargs)
        except ValueError:
            return HttpResponseBadRequest(f"Try again with a valid date.")
        except Http404:
            srg = self.request.GET
            errstring = f"No nests found for Neighborhood or Suburb #{nid}"
            errstring += f"on {srg.get('date', srg.get('rotation', 'today'))}"
            ss = srg.get("pokemon", srg.get("species", srg.get("pokémon", None)))
            if ss:
                errstring += f" matching a search for {ss}"
            errstring += f"."
            return HttpResponseNotFound(errstring)

    def get_context_data(self, **kwargs):
        nid = self.kwargs["neighborhood_id"]
        context = super().get_context_data(**kwargs)
        context["location"] = NstNeighborhood.objects.get(pk=nid)
        context["rotation"] = get_rotation(self.request.GET.get("date", "t"))
        context["neighbor_view"] = True
        context["empties"] = collect_empty_nests(
            context["rotation"], location_type="neighborhood", location_pk=nid
        )
        return context


class ParkViewSet(ListAPIView):
    model = NstLocation
    serializer_class = ParkSerializer

    def get_queryset(self):
        return NstLocation.objects.filter(neighborhood=self.kwargs["city_id"])
