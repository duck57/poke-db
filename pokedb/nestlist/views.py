from django.shortcuts import render, get_object_or_404
from django.http import (
    HttpResponseRedirect,
    HttpResponseBadRequest,
    Http404,
    HttpResponseNotFound,
)
from django.urls import reverse
from django.views import generic
from rest_framework import viewsets
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveAPIView
from django.db.models import Q

# Create your views here.
from .models import (
    NstSpeciesListArchive,
    NstMetropolisMajor,
    NstLocation,
    get_local_nsla_for_rotation,
    NstNeighborhood,
    get_rotation,
)
from speciesinfo.models import match_species_by_name_or_number
from .serializers import ParkSerializer


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
        sp_filter = srg.get("pokemon", srg.get("species", srg.get("pokémon", None)))
        out = get_local_nsla_for_rotation(
            get_rotation(self.kwargs.get("date", "t")), self.kwargs["city_id"], "city"
        )
        if sp_filter is None:
            return out  # no filter
        return out.filter(
            Q(
                species_name_fk__in=match_species_by_name_or_number(
                    sp_txt=sp_filter, previous_evolution_search=True
                )
            )
            | Q(species_txt__icontains=sp_filter)  # for free-text row-matching
        )

    def get(self, request, *args, **kwargs):
        try:
            return super(CityView, self).get(request, *args, **kwargs)
        except ValueError:
            return HttpResponseBadRequest(f"Try again with a valid date.")
        except Http404:
            errstring = f"No nests found for city #{self.kwargs['city_id']} on {self.kwargs.get('date', 'today')}"
            srg = self.request.GET
            ss = srg.get("pokemon", srg.get("species", srg.get("pokémon", None)))
            if ss:
                errstring += f" matching a search for {ss}"
            errstring += f"."
            return HttpResponseNotFound(errstring)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["city"] = NstMetropolisMajor.objects.get(pk=self.kwargs["city_id"])
        context["rotation"] = get_rotation(self.kwargs.get("date", "t"))
        return context


class NeighborhoodIndex(generic.ListView):
    model = NstNeighborhood
    context_object_name = "neighborhood_list"

    def get_queryset(self):
        return NstNeighborhood.objects.filter(major_city=self.kwargs["city_id"])


class IndexView(generic.ListView):
    model = NstMetropolisMajor
    template_name = "nestlist/index.html"
    context_object_name = "city_list"

    def get_queryset(self):
        return NstMetropolisMajor.objects.all()


class NestView(generic.DetailView):
    model = NstLocation
    template_name = "nestlist/nest.html"


class ParkViewSet(ListAPIView):
    model = NstLocation
    serializer_class = ParkSerializer

    def get_queryset(self):
        return NstLocation.objects.filter(neighborhood=self.kwargs["city_id"])
