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
    NstRotationDate,
    NstNeighborhood,
)
from speciesinfo.models import Pokemon, Generation
from typeedit.models import Type
from .serializers import ParkSerializer


def get_rotation(date):
    date = str(date)  # handle both str and int input
    if len(date) < 4 and str_int(date):
        try:
            return NstRotationDate.objects.get(pk=int(date))
        except NstRotationDate.DoesNotExist:
            get_rotation("t")  # default to today if it's junk
    return NstRotationDate.objects.filter(date__lte=parse_date(date)).order_by("-date")[
        0
    ]


def filter_nsla_by_species_name(out, sp_filter):
    q = Pokemon.objects.filter(name="Can't find me!")  # will be useful later

    if len(sp_filter) > 3:  # to prevent "ch" from matching "Psychic"
        # Test by type
        try:
            ts = Type.objects.get(name__icontains=sp_filter)
            return out.filter(
                Q(species_name_fk__type1=ts) | Q(species_name_fk__type2=ts)
            )
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
        # In this if block to prevent excessive results from short queries
        q = Pokemon.objects.filter(name__icontains=sp_filter)
        q2 = q
        for species in q:
            if species.evolved_from:
                p1 = Pokemon.objects.filter(dex_number=species.evolved_from)
                q2 = q2 | p1
                for species1 in p1:
                    if species1.evolved_from:
                        q2 = q2 | Pokemon.objects.filter(
                            dex_number=species1.evolved_from
                        )
        q = q2.exclude(dex_number__in=[0, -999]).distinct()

    # Search by species name
    return out.filter(
        Q(species_txt__icontains=sp_filter)
        | Q(species_name_fk__name__icontains=sp_filter)
        | Q(species_name_fk__in=q)
    )


def filter_nsla_by_species_number(out, sp_filter):
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
    sp_filter = str(sp_filter).strip().lower()
    if "start" in sp_filter:
        return out.filter(
            species_name_fk__category=50
        )  # Starter Pokémon are category 50
    if str_int(sp_filter):  # numbers search by Pokédex number
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
        sp_filter = srg.get("pokemon", srg.get("species", srg.get("pokémon", None)))
        out = NstSpeciesListArchive.objects.filter(
            nestid__neighborhood__major_city=self.kwargs["city_id"],
            rotation_num=get_rotation(self.kwargs.get("date", "t")),
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
            errstring = f"No nests found for city #{self.kwargs['city_id']} on {self.kwargs.get('date', 'today')}"
            srg = self.request.GET
            ss = srg.get("pokemon", srg.get("species", srg.get("pokémon", None)))
            if ss:
                errstring += f" matching a search for {ss}"
            errstring += f"."
            return HttpResponseNotFound(errstring)


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
