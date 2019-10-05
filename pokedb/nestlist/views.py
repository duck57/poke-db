from django.shortcuts import render
from django.http import (
    HttpResponseRedirect,
    HttpResponseBadRequest,
    Http404,
    HttpResponseNotFound,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveAPIView
from .utils import parse_date, str_int
from django.db.models import Q

# Create your views here.
from .models import (
    NstSpeciesListArchive,
    NstMetropolisMajor,
    NstLocation,
    NstCombinedRegion,
    NstNeighborhood,
    get_rotation,
)
from speciesinfo.models import Pokemon, Generation
from typeedit.models import Type
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


def filter_nsla_by_species_name(out, sp_filter):
    """

    :param out:
    :param sp_filter:
    :return:
    """

    if len(sp_filter) < 3:  # handle short queries
        return out.filter(
            Q(species_txt__icontains=sp_filter)
            | Q(species_name_fk__name__icontains=sp_filter)
        )  # refactored to minimize the amount of indented code

    # Test by type
    """Note how there needs to be at least 3 characters in the query
    to reach here.  This is to prevent 'ch' from matching 'Psychic'."""
    try:
        ts = Type.objects.get(name__icontains=sp_filter)
        return out.filter(Q(species_name_fk__type1=ts) | Q(species_name_fk__type2=ts))
    except Type.DoesNotExist:
        pass
    except Type.MultipleObjectsReturned:
        pass

    # Test by region/generation
    try:
        gen = Generation.objects.get(region__icontains=sp_filter)
        return out.filter(species_name_fk__generation=gen)
    except Generation.DoesNotExist:
        pass
    except Generation.MultipleObjectsReturned:
        pass

    # Gather previous generations
    """This is after the short query filter to keep results at a 
    reasonable length."""
    q = Pokemon.objects.filter(name__icontains=sp_filter)
    q2 = q
    for species in q:
        if species.evolved_from:
            p1 = Pokemon.objects.filter(dex_number=species.evolved_from)
            q2 = q2 | p1
            for species1 in p1:
                if species1.evolved_from:
                    q2 = q2 | Pokemon.objects.filter(dex_number=species1.evolved_from)
    q = q2.exclude(dex_number__in=[0, -999]).distinct()

    # Search by species name
    return out.filter(
        Q(species_txt__icontains=sp_filter)
        | Q(species_name_fk__name__icontains=sp_filter)
        | Q(species_name_fk__in=q)
    )


def filter_nsla_by_species_number(out, sp_filter):
    """

    :param out:
    :param sp_filter:
    :return:
    """
    try:
        # matching for previous evolutions so you can search for the number of the evolved form
        q = Pokemon.objects.get(dex_number=sp_filter, form="Normal")
        p1 = Pokemon.objects.get(dex_number=q.evolved_from, form="Normal")
        p0 = Pokemon.objects.get(dex_number=p1.evolved_from, form="Normal")

        # don't match so far back as to hit nests of commons
        if p1.dex_number == 0:
            p1 = Pokemon.objects.get(dex_number=-999)
        if p0.dex_number == 0:
            p1 = Pokemon.objects.get(dex_number=-999)
    except Pokemon.DoesNotExist:
        return out.filter(species_name_fk__dex_number=sp_filter)
    return out.filter(
        Q(species_name_fk__dex_number=sp_filter)
        | Q(species_name_fk=p1)
        | Q(species_name_fk=p0)
    )


def filter_nsla(out, sp_filter):
    """

    :param out:
    :param sp_filter:
    :return:
    """
    sp_filter = str(sp_filter).strip().lower()
    if sp_filter == "abra":
        # hardcode Abra so Crabwaler doesn't match®
        return out.filter(
            Q(species_name_fk="Abra") | Q(species_txt__lower="abra") | Q(species_no=63)
        )
    if "start" in sp_filter:
        return out.filter(
            species_name_fk__category=50
        )  # Starter Pokémon are category 50
    if str_int(sp_filter):  # numeric queries search by Pokédex number
        return filter_nsla_by_species_number(out, sp_filter)
    return filter_nsla_by_species_name(out, sp_filter)


class CityView(generic.ListView):
    model = NstSpeciesListArchive
    template_name = "nestlist/city.html"
    context_object_name = "current_nest_list"
    pk_url_kwarg = "city_id"
    allow_empty = False

    def get_queryset(self):
        srg = self.request.GET
        # handle both /rotation/<date> and ?date=yyyy-mm-dd formats
        date = self.kwargs.get("date", srg.get("date", srg.get("rotation", "t")))
        sp_filter = srg.get("pokemon", srg.get("species", srg.get("pokémon", None)))
        out = NstSpeciesListArchive.objects.filter(
            nestid__neighborhood__major_city=self.kwargs["city_id"],
            rotation_num=get_rotation(date),
        ).order_by("nestid__official_name")
        if sp_filter is None:
            return out  # no filter
        return filter_nsla(out, sp_filter)

    def get(self, request, *args, **kwargs):
        try:
            return super(CityView, self).get(request, *args, **kwargs)
        except ValueError:
            return HttpResponseBadRequest(f"Try again with a valid date.")
        except Http404:
            srg = self.request.GET
            errstring = f"No nests found for city #{self.kwargs['city_id']} on {srg.get('date', srg.get('rotation', 'today'))}"
            ss = srg.get("pokemon", srg.get("species", srg.get("pokémon", None)))
            if ss:
                errstring += f" matching a search for {ss}"
            errstring += f"."
            return HttpResponseNotFound(errstring)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["location"] = NstMetropolisMajor.objects.get(pk=self.kwargs["city_id"])
        context["rotation"] = get_rotation(self.kwargs.get("date", "t"))
        context["title"] = "List of Nest Databases"
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


class ParkViewSet(ListAPIView):
    model = NstLocation
    serializer_class = ParkSerializer

    def get_queryset(self):
        return NstLocation.objects.filter(neighborhood=self.kwargs["city_id"])
