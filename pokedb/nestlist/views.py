from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponseBadRequest, Http404, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from rest_framework import viewsets
from .utils import parse_date, str_int
from django.db.models import Q

# Create your views here.
from .models import (
    NstSpeciesListArchive,
    NstMetropolisMajor,
    NstLocation,
    NstRotationDate,
)
from speciesinfo.models import Pokemon, Generation
from typeedit.models import Type


class CityView(generic.ListView):
    model = NstSpeciesListArchive
    template_name = "nestlist/city.html"
    context_object_name = "current_nest_list"
    pk_url_kwarg = "city_id"
    allow_empty = False

    def get_rotation(self, date):
        return NstRotationDate.objects.filter(date__lte=parse_date(date)).order_by(
            "-num"
        )[0]

    def get_queryset(self):
        srg = self.request.GET
        sp_filter = srg.get("pokemon", srg.get("species", srg.get("pokémon", None)))

        # this may raise a ValueError
        out = NstSpeciesListArchive.objects.filter(
            nestid__neighborhood__major_city=self.kwargs["city_id"],
            rotation_num=self.get_rotation(self.kwargs.get("date", "t")),
        ).order_by("nestid__official_name")

        if sp_filter is None:
            return out
        sp_filter = sp_filter.strip().lower()
        if "start" in sp_filter:
            return out.filter(
                species_name_fk__category=50
            )  # Starter Pokémon are category 50
        if str_int(sp_filter):  # numbers search by Pokédex number
            return out.filter(species_name_fk__dex_number=sp_filter)
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

        # Search by species name
        return out.filter(
            Q(species_txt__icontains=sp_filter)
            | Q(species_name_fk__name__icontains=sp_filter)
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


class IndexView(generic.ListView):
    model = NstMetropolisMajor
    template_name = "nestlist/index.html"
    context_object_name = "city_list"

    def get_queryset(self):
        return NstMetropolisMajor.objects.all()


class NestView(generic.DetailView):
    model = NstLocation
    template_name = "nestlist/nest.html"


class ParkViewSet(viewsets.ModelViewSet):
    model = NstLocation
