from typing import Dict, List, Union

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
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
    NstRotationDate,
    add_a_report,
)
from .serializers import ParkSerializer
from .forms import NestReportForm


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
                name=cd["your_name"],
                bot_id=city.airtable_bot.pk,
                nest=cd["park"],
                species=cd["species"],
                timestamp=cd["timestamp"],
                server="🕸",
            )

            if submission_status.status != 9:
                # redirect to a new URL:
                return HttpResponseRedirect(
                    reverse(
                        "nestlist:thank_you",
                        kwargs={"city_id": city.pk, "status": submission_status.status},
                    )
                )
            else:
                pass  # add stuff to the form validation later

    # if a GET (or any other method) we'll create a blank form
    else:
        form = NestReportForm()

    return render(
        request, "nestlist/report-form.jinja", {"form": form, "location": city}
    )


def thank_you(request, **kwargs):
    return render(
        request,
        "nestlist/thankyou.jinja",
        {
            "location": NstMetropolisMajor.objects.get(pk=kwargs["city_id"]),
            "status": kwargs["status"],
        },
    )


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
        scope: str = self.kwargs["scope"]
        pk: Union[str, int] = self.kwargs[self.kwargs["pk_name"]]
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
            errstring: str = f"No nests found for {scope} #{pk}"
            if scope != "nest":
                errstring += f" on {self.get_rot8()}"
            ss: str = self.get_sp()
            if ss:
                errstring += f" matching a search for {ss}"
            errstring += f"."
            return HttpResponseNotFound(errstring)

    def get_context_data(self, **kwargs) -> Dict:
        """
        This dude could probably be refactored, perhaps into subclasses
        :return: context data with all the fun bits the specific templates expect
        """
        context = super().get_context_data(**kwargs)
        scope: str = self.kwargs["scope"]
        pk: Union[str, int] = self.kwargs[self.kwargs["pk_name"]]
        context["location"] = self.model_list[scope].objects.get(pk=pk)
        context["rotation"]: NstRotationDate = self.get_rot8()
        if scope == "neighborhood":
            context["neighbor_view"]: bool = True
            context["empties"]: "QuerySet[NstLocation]" = collect_empty_nests(
                rotation=context["rotation"],
                location_type="neighborhood",
                location_pk=pk,
            )
        elif scope == "nest":
            nest: NstLocation = context["location"]
            context["nest_view"]: bool = True
            context["other_names"]: List[str] = [
                nest.short_name
            ] if nest.short_name else []
            for name in nest.alternate_name.exclude(hide_me=True):
                context["other_names"].append(name.name)
        if self.kwargs.get("history"):
            context["history"]: bool = True
            if self.kwargs.get("species_detail"):
                sp: str = self.kwargs["poke"]
                context["species_count"]: int = (
                    species_nesting_history(sp=sp, city=pk)
                    .values("species_name_fk")
                    .distinct()
                    .count()
                )
                context["species_name"]: str = (
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
        return context


class ParkViewSet(ListAPIView):
    model = NstLocation
    serializer_class = ParkSerializer

    def get_queryset(self):
        return NstLocation.objects.filter(neighborhood=self.kwargs["city_id"])


class NestDetail(RetrieveAPIView):
    model = NstLocation
    serializer_class = ParkSerializer
    pass
