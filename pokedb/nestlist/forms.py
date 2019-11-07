from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from nestlist.models import query_nests, NstNeighborhood, NstCombinedRegion
from nestlist.utils import parse_date
from speciesinfo.models import (
    match_species_by_name_or_number,
    enabled_in_pogo,
    nestable_species,
)
from typing import Dict, Any

MAGIC_NEWLINE = f" gnbgkas "
QUOT_L = f"«"
QUOT_R = f"»"


def pokemon_validator(value, isl=enabled_in_pogo(nestable_species())):
    match_count: int = match_species_by_name_or_number(
        sp_txt=value,
        only_one=True,
        input_set=isl,
        age_up=True,
        previous_evolution_search=True,
    ).count()
    stem: str = f"⚠️{QUOT_L}{value}{QUOT_R} "
    if match_count == 0:
        raise ValidationError(stem + f"did not match any pokémon.")
    elif match_count > 1:
        raise ValidationError(
            stem
            + f"matched {match_count} pokémon.{MAGIC_NEWLINE}  Please be more specific."
        )


def park_validator(value, place=None, restrict_city: bool = False, scope: str = "city"):
    match_count: int = query_nests(
        value, location_id=place, location_type=scope, only_one=True
    ).count()
    err_str: str = f"⚠️{QUOT_L}{value}{QUOT_R} "
    if match_count == 0:
        err_str += f"did not match any nests in {scope} #{place.pk}." + MAGIC_NEWLINE
        err_str += f"\nIf you are sure {QUOT_L}{value}{QUOT_R} is the proper spelling and in the correct {scope}, "
        err_str += "please contact a nest master."
        raise ValidationError(err_str)
    if restrict_city and match_count > 1:
        err_str += f"matched {match_count} nests when a unique match was required."
        err_str += MAGIC_NEWLINE + f"\nPlease be more specific."
        raise ValidationError(err_str)


def date_validator(value):
    try:
        g = parse_date(value)
    except ValueError:
        raise ValidationError(f"⚠️{QUOT_L}{value}{QUOT_R} is an invalid date.")
    if g > timezone.now():
        raise ValidationError(
            f"👽Support for time-travelling players has yet to be implemented."
        )


class NestReportForm(forms.Form):
    def __init__(self, request=None, city=None):
        super(NestReportForm, self).__init__(request)
        self.city = city

    your_name = forms.CharField(
        label="Your name",
        max_length=100,
        help_text="Who are you?",
        widget=forms.TextInput(
            attrs={
                "placeholder": "It doesn't matter if you use your trainer name, e-mail, \
Discord handle, Facebook name, or phone number \
so long as you're consistent.",
                "alt": "test12",
                "autofill": True,
            }
        ),
    )
    neighborhood = forms.CharField(
        label="Neighborhood",
        required=False,
        help_text="Which part of town?",
        widget=forms.TextInput(attrs={"placeholder": "Option to refine park results."}),
    )
    park = forms.CharField(
        label="Park", validators=[park_validator], help_text="Where were you?"
    )
    species = forms.CharField(
        label="Species", validators=[pokemon_validator], help_text="What did you see?"
    )
    timestamp = forms.CharField(
        label="time of sighting",
        initial=parse_date("h-1").strftime("%Y-%m-%d %H:%M"),
        help_text="When were they seen?",
        # widget=forms.TextInput(attrs={"placeholder": "When were you?"}),
        validators=[date_validator],
    )

    def clean(self) -> Dict[str, Any]:
        # filter parks within the city
        cd: Dict = self.cleaned_data

        # nest filtering for specific places
        place = cd.get("neighborhood")
        complete: bool = False
        scope: str = ""
        if place and not complete:
            try:
                place = NstNeighborhood.objects.get(
                    name__istartswith=place, major_city=self.city
                )
                scope = "neighborhood"
                complete = True
            except NstNeighborhood.DoesNotExist:
                pass
            except NstNeighborhood.MultipleObjectsReturned:
                pass
        if place and not complete:
            try:
                place = NstCombinedRegion.objects.get(name__icontains=place)
                complete = True
                scope = "region"
            except NstCombinedRegion.DoesNotExist:
                pass
            except NstCombinedRegion.MultipleObjectsReturned:
                pass
        if place and not complete:
            est: str = f"ℹ️{QUOT_L}{place}{QUOT_R} did not match a unique neighborhood or region."
            est += (
                MAGIC_NEWLINE
                + f"Searching all of {self.city.short_name} as if this were left empty."
            )
            self.add_error("neighborhood", est)
        if not complete:
            place, scope = self.city, "city"

        # check if the park is hooked up
        try:
            park_validator(
                value=cd["park"], place=place, restrict_city=True, scope=scope
            )
        except ValidationError as ve:
            self.add_error("park", ve)
        except KeyError:
            pass
        cd["subplace"]: int = place.pk
        cd["scope"] = scope

        try:
            cd["timestamp"] = parse_date(cd["timestamp"])
        except KeyError:
            pass
        return cd
