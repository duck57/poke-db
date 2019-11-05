from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from nestlist.models import query_nests
from nestlist.utils import parse_relative_date, parse_date
from speciesinfo.models import (
    match_species_by_name_or_number,
    enabled_in_pogo,
    nestable_species,
)


def pokemon_validator(value):
    match_count = match_species_by_name_or_number(
        sp_txt=value,
        only_one=True,
        input_set=enabled_in_pogo(nestable_species()),
        age_up=True,
        previous_evolution_search=True,
    ).count()
    if match_count != 1:
        raise ValidationError(f"{value} matched {match_count} pokémon instead of 1")


def park_validator(value, place=None):
    match_count = query_nests(value, location_id=place, location_type="city").count()
    if match_count != 1:
        errstr: str = f"{value} matched {match_count} nests instead of 1"
        errstr += "\nIf you are sure it is spelled correctly and in the right city, please contact a nest master"
        raise ValidationError(errstr)


def date_validator(value):
    try:
        g = parse_date(value)
    except ValueError:
        raise ValidationError(f"{value} is an invalid date")
    if g > timezone.now():
        raise ValidationError(
            f"Support for time-travelling players has yet to be implemented"
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
    park = forms.CharField(
        label="Park", validators=[park_validator], help_text="Where were you?"
    )
    species = forms.CharField(
        label="Species", validators=[pokemon_validator], help_text="What did you see?"
    )
    timestamp = forms.CharField(
        label="time of sighting",
        initial=parse_relative_date("h-1").strftime("%Y-%m-%d %H:%M"),
        help_text="When were they seen?",
        # widget=forms.TextInput(attrs={"placeholder": "When were you?"}),
        validators=[date_validator],
    )
