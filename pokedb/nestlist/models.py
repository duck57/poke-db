"""
Models for the nest list

After all the class-based models are the static methods for dealing with the models
which will prove useful all over the place.
"""

from abc import abstractmethod
from datetime import datetime
from math import radians, pi
from typing import Union, Optional, Tuple, NamedTuple, Dict, Type, List

from django.conf import settings
from django.db import models
from django.db.models import Q, F, Case, When
from django.db.models.functions import (
    Power,
    Sin,
    Cos,
    ATan2,
    Sqrt,
    Radians,
    Lower,
    Degrees,
    Mod,
    Tan,
    Ln,
)
from django.db.models.query import QuerySet
from django.urls import reverse
from django.core.validators import MaxValueValidator, MinValueValidator
from djchoices import DjangoChoices, ChoiceItem

from speciesinfo.models import (
    match_species_by_name_or_number,
    Pokemon,
    nestable_species,
    get_surrounding_species,
    enabled_in_pogo,
    self_as_qs,
)
from .utils import (
    parse_date,
    str_int,
    append_utc,
    true_if_y,
    initial_bearing,
    angle_between_points_on_sphere,
    cv_geo_tuple,
    cardinal_direction_from_bearing,
    EARTH_RADIUS,
    loxo_len,
    constant_bearing_between_points_on_sphere,
)

from s2sphere import CellId, LatLng

APP_PREFIX: str = "nestlist"  # is there some way to import this dynamically?


def make_url_name(name: str) -> str:
    """For Django reverse URL lookup"""
    return APP_PREFIX + ":" + name


def url_reverser(rev_name: str, params: Dict):
    return reverse(make_url_name(rev_name), kwargs=params)


class Place:
    pk: int

    @abstractmethod
    def city_q(self) -> Q:
        pass

    @abstractmethod
    def neighborhood_q(self) -> Q:
        pass

    @abstractmethod
    def region_q(self) -> Q:
        pass

    @abstractmethod
    def ps_q(self) -> Q:
        pass

    @abstractmethod
    def nest_q(self) -> Q:
        pass

    def city_list(self) -> "QuerySet[NstMetropolisMajor]":
        return place_filter(NstMetropolisMajor, self.city_q())

    def neighborhood_list(self) -> "QuerySet[NstNeighborhood]":
        return place_filter(NstNeighborhood, self.neighborhood_q())

    def region_list(self) -> "QuerySet[NstCombinedRegion]":
        return place_filter(NstCombinedRegion, self.region_q())

    def park_system_list(self) -> "QuerySet[NstParkSystem]":
        return place_filter(NstParkSystem, self.ps_q())

    def park_list(self) -> "QuerySet[NstLocation]":
        return place_filter(NstLocation, self.nest_q())

    def rot_q(self) -> Q:
        return Q(nstspecieslistarchive__nestid__in=self.park_list())

    def active_rotations(self) -> "QuerySet[NstRotationDate]":
        return place_filter(NstRotationDate, self.rot_q())

    def pretty_nearby_list(self, radius: float) -> "Dict[str, List]":
        """
        This is only here to prevent errors.
        GeoCoordMixin has the correct implementation.
        :param radius: set negative to use as an exclusion zone
        """
        return dict(self_as_qs(self).exclude(pk=self.pk)[: int(radius)])


def place_filter(model: Type[models.Model], q: Q) -> "QuerySet":
    return model.objects.filter(q).distinct()


class HasURLMixin:
    """
    Models that should have web_url and api_url methods:
    NstLocation
    NSLA
    NstRawRpt
    NstMetropolisMajor
    NstCombinedRegion
    NstNeighborhood
    NstParkSystem
    """

    @abstractmethod
    def web_url(self):
        pass

    @abstractmethod
    def api_url(self):
        pass


class HasCityMixin:
    """
    Models that need a ct() method:
    NstLocation
    NSLA
    NstNeighborhood
    NstMetropolisMajor
    """

    @abstractmethod
    def ct(self):
        pass


class ComplicatedNameMixin:
    """
    Models that should have get_name, full_name, and short_name:
    NstLocation
    NstMetropolisMajor
    NstParkSystem
    NstCombinedRegion
    NstNeighborhood
    """

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def full_name(self) -> str:
        pass

    @abstractmethod
    def short_name(self) -> str:
        pass


class LocationQuerySet(models.QuerySet):
    def within_y_km(
        self,
        current_lat: float,
        current_long: float,
        y_km: float,
        *,
        use_rhumb: bool = False,
    ):
        """
        Annotations are for orthodrome, loxodrome (rhumb) on both the bearing
        (initial & constant) and the distance
        :param use_rhumb: run these calculations with rhumb lines instead of great circles
                      always a named param
        :param current_lat: IN DEGREES
        :param current_long: IN DEGREES
        :param y_km: set negative to create an exclusion radius instead
        :return: the other locations of the same type within y_km
        """

        # General set-up
        #
        # current = _1 variables (here)
        # test = _2 variables (there)
        current_lat = Radians(current_lat)
        current_long = Radians(current_long)
        test_lat = Radians(F("lat"))
        test_long = Radians(F("lon"))
        dlat = test_lat - current_lat
        dlong = test_long - current_long
        sort_field: str = "rhumb_len" if use_rhumb else "distance"

        def to_bearing(x, y):
            return Mod(Degrees(ATan2(x, y)) + 360, 360)

        filter_func: Q = {
            (True, True): Q(rhumb_len__gt=abs(y_km)),
            (True, False): Q(distance__gt=abs(y_km)),
            (False, True): Q(rhumb_len__lte=y_km),
            (False, False): Q(distance__lte=y_km),
        }.get((y_km < 0, use_rhumb), Q())

        #
        # Calculations
        #

        # Distance
        a = Power(Sin(dlat / 2), 2) + Cos(current_lat) * Cos(test_lat) * Power(
            Sin(dlong / 2), 2
        )
        c = 2 * ATan2(Sqrt(a), Sqrt(1 - a))
        distance = EARTH_RADIUS * c

        # Initial bearing annotation
        numerator = Sin(dlong) * Cos(test_lat)
        denominator = Cos(current_lat) * Sin(test_lat) - Sin(current_lat) * Cos(
            test_lat
        ) * Cos(dlong)
        forward_azimuth = to_bearing(numerator, denominator)

        # Loxo common calculations
        d_lon = Mod(dlong + 3 * pi, 2 * pi) - pi
        dpsi = Ln(Tan(pi / 4 + test_lat / 2) / Tan(pi / 4 + current_lat / 2))

        # Rhumb direction
        constant_bearing = to_bearing(d_lon, dpsi)

        # Loxodrome distance
        q = Case(
            When(
                lat__lt=Degrees(current_lat) + 9e-9,
                lat__gt=Degrees(current_lat) - 9e-9,
                then=Cos(current_lat),
            ),
            default=dlat / dpsi,
        )
        loxo_km = Sqrt(dlat * dlat + q * q * d_lon * d_lon) * EARTH_RADIUS

        return (
            self.annotate(distance=distance)
            .annotate(rhumb_len=loxo_km)
            .order_by(sort_field)
            .filter(filter_func)
            .annotate(bearing_initial=forward_azimuth)
            .annotate(bearing_constant=constant_bearing)
        )


class GeoCoordMixin:
    """
    Mixin for dealing with objects with coordinates
    """

    # Both are stored as degrees
    # Validators are to prevent trig functions from dividing by zero
    lat = models.FloatField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(90), MinValueValidator(-90)],
    )
    lon = models.FloatField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(180), MinValueValidator(-180)],
    )
    objects = LocationQuerySet.as_manager()
    pk: int

    class Meta:
        abstract = True

    def coord_tuple(self) -> Optional[Tuple[float, float]]:
        if isinstance(self.lat, float) and isinstance(self.lon, float):
            return self.lat, self.lon
        return None

    def initial_bearing_deg(self, elsewhere) -> Optional[float]:
        """
        :param elsewhere: another GeoCoordMixin instance
        :return: the initial bearing in degrees (0° is North, clockwise)
        """
        here = self.coord_tuple()
        there = elsewhere.coord_tuple()
        if here is None or there is None:
            return None
        return initial_bearing(here, there)

    def distance_to_rad(self, elsewhere) -> Optional[float]:
        here = cv_geo_tuple(self.coord_tuple(), radians)
        there = cv_geo_tuple(elsewhere.coord_tuple(), radians)
        if here is None or there is None:
            return None
        return angle_between_points_on_sphere(here, there, in_radians=True)

    def nav_to(self, elsewhere: "GeoCoordMixin") -> Optional[Dict[str, float]]:
        """This could be rewritten as a nasty one-liner"""
        here = cv_geo_tuple(self.coord_tuple(), radians)
        there = cv_geo_tuple(elsewhere.coord_tuple(), radians)
        if here is None or there is None:
            return None
        return {
            "angle_between_radians": angle_between_points_on_sphere(
                here, there, out_radians=True
            ),
            "angle_between_degrees": angle_between_points_on_sphere(
                here, there, out_radians=False
            ),
            "initial_bearing_degrees": initial_bearing(
                here, there, in_radians=True, out_radians=False
            ),
            "initial_bearing_radians": initial_bearing(
                here, there, in_radians=True, out_radians=True
            ),
            "great_circle_km": angle_between_points_on_sphere(here, there)
            * EARTH_RADIUS,
            "loxodrome_km": loxo_len(here, there),
            "constant_bearing_degrees": constant_bearing_between_points_on_sphere(
                here, there, out_radians=False
            ),
            "constant_bearing_radians": constant_bearing_between_points_on_sphere(
                here, there, out_radians=True
            ),
        }

    def distance_to_km(self, elsewhere) -> Optional[float]:
        return self.distance_to_rad(elsewhere) * EARTH_RADIUS

    def nearby(self, radius: float, *, use_rhumb: bool = False) -> LocationQuerySet:
        """
        :param use_rhumb:
        :param radius: search radius.  set negative to use an an exclusion radius
        :return: a QS of nearby objects of the same type
        """
        if not self.coord_tuple():
            return self_as_qs(None)
        return (
            type(self)
            .objects.within_y_km(self.lat, self.lon, radius, use_rhumb=use_rhumb)
            .exclude(pk=self.pk)
        )

    def pretty_nearby_list(
        self,
        radius: float,
        *,
        use_rhumb_distance: bool = False,
        use_rhumb_direction: bool = True,
    ) -> "Dict[str, List]":
        """
        Pre-formats the nearby location square on the web page
        """
        o: Dict[str, List] = {}
        for p in self.nearby(radius, use_rhumb=use_rhumb_distance):
            d = cardinal_direction_from_bearing(
                p.bearing_constant if use_rhumb_direction else p.direction
            )
            if not o.get(d):
                o[d] = [p]
            else:
                o[d].append(p)
        return o

    def s2id(self, level: int = 17) -> CellId:
        if level < 0:
            level = 10
        if level > 30:
            level = 20
        at = self.lat
        on = self.lon
        if hasattr(self, "neighborhood"):
            if at is None:
                at = self.neighborhood.lat
            if on is None:
                on = self.neighborhood.lon
        if hasattr(self, "city"):
            if at is None:
                at = self.city.lat
            if on is None:
                on = self.city.lon
        return CellId.from_lat_lng(LatLng.from_degrees(at, on)).parent(level)


class NstAdminEmail(models.Model, ComplicatedNameMixin, HasCityMixin):
    class UserType(DjangoChoices):
        human = ChoiceItem(0)
        system = ChoiceItem(2)
        survey = ChoiceItem(1)
        scanner = ChoiceItem(3)

    name = models.CharField(max_length=90)
    city = models.ForeignKey(
        "NstMetropolisMajor",
        on_delete=models.SET_NULL,
        db_column="city",
        blank=True,
        null=True,
    )
    shortname = models.CharField(max_length=20, blank=True, null=True)
    auth_user = models.OneToOneField(
        "auth.user",
        on_delete=models.SET_NULL,
        related_name="nest_user",
        null=True,
        blank=True,
    )
    is_bot = models.PositiveSmallIntegerField(
        null=True, blank=False, default=UserType.survey, choices=UserType.choices
    )

    class Meta:
        db_table = "nst_admin_email"

    def __str__(self):
        return f"{self.get_name()} [{self.UserType.values[self.is_bot]}]"

    def restricted(self) -> bool:
        return (
            False
            if self.is_bot in [self.UserType.human, self.UserType.system]
            else True
        )

    def get_name(self):
        return self.shortname if self.shortname else self.name

    def short_name(self):
        return self.shortname

    def full_name(self) -> str:
        return self.name

    def ct(self):
        return self.city


class NstAltName(models.Model):
    name = models.CharField(max_length=222)
    main_entry = models.ForeignKey(
        "NstLocation",
        models.DO_NOTHING,
        db_column="main_entry",
        related_name="alternate_name",
    )
    hide_me = models.BooleanField(db_column="hideme", default=False)
    id = models.AutoField(primary_key=True, db_column="dj_key")

    class Meta:
        db_table = "nst_alt_name"

    def __str__(self):
        if self.hide_me:
            return f"[hidden, id={self.id}]"
        return f"{self.name} [{self.main_entry.get_name()}]"


class NstCombinedRegion(models.Model, ComplicatedNameMixin, HasURLMixin, Place):
    name = models.CharField(max_length=222)

    class Meta:
        db_table = "nst_combined_region"

    def __str__(self):
        return f"{self.name} [{self.pk}]"

    def __lt__(self, other):
        return self.name < other.name

    def __cmp__(self, other):
        if self.name == other.name:
            return 0
        if self < other:
            return -1
        return 1

    def short_name(self):
        return self.name

    def get_name(self):
        return self.name

    def full_name(self):
        return self.name

    def web_url(self):
        return url_reverser("region", {"region_id": self.pk})

    def api_url(self):
        return url_reverser("region_api", {"region_id": self.pk})

    def city_q(self) -> Q:
        return Q(nstneighborhood__region=self)

    def neighborhood_q(self) -> Q:
        return Q(pk__in=self.neighborhood_list())

    def neighborhood_list(self) -> "QuerySet[NstNeighborhood]":
        if hasattr(self, "neighborhoods"):  # make the lint shut up
            return self.neighborhoods.all()
        return NstNeighborhood.objects.none()

    def region_q(self) -> Q:
        return Q(pk=self)

    def region_list(self) -> "QuerySet[NstCombinedRegion]":
        return self_as_qs(self)

    def ps_q(self) -> Q:
        return Q(nstlocation__neighborhood__region=self)

    def nest_q(self) -> Q:
        return Q(neighborhood__region=self)


class NstLocation(
    models.Model, GeoCoordMixin, ComplicatedNameMixin, HasCityMixin, HasURLMixin, Place
):
    objects = LocationQuerySet.as_manager()
    nestID = models.AutoField(primary_key=True, db_column="nest_id")
    official_name = models.CharField(max_length=222)
    short_name = models.CharField(max_length=222, blank=True, null=True)
    neighborhood = models.ForeignKey(
        "NstNeighborhood",
        models.DO_NOTHING,
        db_column="location",
        blank=True,
        null=True,
    )
    address = models.CharField(max_length=234, blank=True, null=True)
    notes = models.CharField(max_length=234, blank=True, null=True)
    private = models.BooleanField(blank=True, null=True)
    permanent_species = models.CharField(max_length=111, blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    lon = models.FloatField(blank=True, null=True)
    size = models.IntegerField(blank=True, null=True)
    density = models.IntegerField(blank=True, null=True)
    primary_silph_id = models.IntegerField(blank=True, null=True)
    osm_id = models.IntegerField(db_column="OSM_id", blank=True, null=True)
    park_system = models.ForeignKey(
        "NstParkSystem",
        models.DO_NOTHING,
        db_column="park_system",
        null=True,
        blank=True,
    )
    resident_history = models.ManyToManyField(
        "NstRotationDate", through="NstSpeciesListArchive", symmetrical=True
    )
    duplicate_of = models.ForeignKey(
        "NstLocation",
        models.SET_NULL,
        db_column="duplicate_of",
        null=True,
        blank=True,
        related_name="prior_entries",
    )

    search_fields = ["nestID", "official_name", "short_name", "alternate_name"]

    class Meta:
        db_table = "nst_location"

    def __str__(self):
        return f"{self.official_name} [{self.nestID}] ({self.neighborhood})"

    def get_name(self):
        return self.short_name if self.short_name else self.official_name

    def full_name(self):
        return self.official_name

    def __cmp__(self, other):
        if self.official_name < other.official_name:
            return -1
        if self.official_name > other.official_name:
            return 1
        return 0  # this should not happen

    def __lt__(self, other):
        return self.official_name < other.official_name

    def get_self(self):
        """For duplicate nest handling"""
        return self.duplicate_of if self.duplicate_of else self

    def ct(self):
        return self.neighborhood.major_city

    def web_url(self):
        return url_reverser(
            "nest_history", {"city_id": self.ct().pk, "nest_id": self.pk}
        )

    def api_url(self):
        return url_reverser(
            "nest_api_detail", {"city_id": self.ct().pk, "nest_id": self.pk}
        )

    def active_rotations(self) -> "QuerySet[NstRotationDate]":
        return park_nesting_history(self).values_list("rotation_num")

    def nest_q(self) -> Q:
        return Q(pk=self)

    def park_list(self) -> "QuerySet[NstLocation]":
        return self_as_qs(self)

    def ps_q(self) -> Q:
        return Q(nstlocation=self)

    def park_system_list(self) -> "QuerySet[NstParkSystem]":
        return self_as_qs(self.park_system)

    def city_q(self) -> Q:
        return Q(neighborhood__nstlocation=self)

    def city_list(self) -> "QuerySet[NstMetropolisMajor]":
        return self_as_qs(self.ct())

    def neighborhood_q(self) -> Q:
        return Q(nstlocation=self)

    def neighborhood_list(self) -> "QuerySet[NstNeighborhood]":
        return self_as_qs(self.neighborhood)

    def region_q(self):
        return Q(neighborhood__location=self)

    def region_list(self) -> "QuerySet[NstCombinedRegion]":
        return self.neighborhood.region_list()

    def s2id(self, level: int = 14) -> CellId:
        return super().s2id(level)


class NstMetropolisMajor(
    models.Model, HasCityMixin, HasURLMixin, ComplicatedNameMixin, GeoCoordMixin, Place
):
    name = models.CharField(db_column="Name", max_length=123)
    short_name = models.CharField(
        db_column="Shortname", max_length=88, blank=True, null=True
    )
    lat = models.FloatField(blank=True, null=True)
    lon = models.FloatField(blank=True, null=True)
    note = models.CharField(max_length=255, blank=True, null=True)
    admin_names = models.CharField(max_length=255, blank=True, null=True)
    airtable_base_id = models.CharField(max_length=30, blank=True, null=True)
    airtable_bot = models.ForeignKey(NstAdminEmail, models.SET_NULL, null=True)
    active = models.BooleanField(default=False)
    objects = LocationQuerySet.as_manager()

    class Meta:
        db_table = "nst_metropolis_major"

    def __str__(self):
        return self.name

    def web_url(self):
        return url_reverser("city", {"city_id": self.pk})

    def api_url(self):
        return url_reverser("city_api_view", {"city_id": self.pk})

    def full_name(self):
        return self.name

    def get_name(self):
        return self.name

    def ct(self):
        return self

    def report_form_url(self):
        return url_reverser("report_nest", {"city_id": self.pk})

    def city_q(self) -> Q:
        return Q(pk=self)

    def city_list(self) -> "QuerySet[NstMetropolisMajor]":
        return self_as_qs(self)

    def neighborhood_q(self) -> Q:
        return Q(major_city=self)

    def region_q(self) -> Q:
        return Q(neighborhoods__major_city=self)

    def ps_q(self) -> Q:
        return Q(nstlocation__neighborhood__major_city=self)

    def nest_q(self) -> Q:
        return Q(neighborhood__major_city=self)

    def s2id(self, level: int = 10) -> CellId:
        return super().s2id(level)


class NstNeighborhood(
    models.Model, HasCityMixin, HasURLMixin, ComplicatedNameMixin, GeoCoordMixin, Place
):
    name = models.CharField(max_length=222)
    region = models.ManyToManyField(
        to="NstCombinedRegion", blank=True, related_name="neighborhoods"
    )
    lat = models.FloatField(blank=True, null=True)
    lon = models.FloatField(blank=True, null=True)
    major_city = models.ForeignKey(
        NstMetropolisMajor,
        models.DO_NOTHING,
        db_column="major_city",
        blank=True,
        null=True,
    )
    objects = LocationQuerySet.as_manager()

    class Meta:
        db_table = "nst_neighborhood"

    def __str__(self):
        return self.name

    def web_url(self):
        return url_reverser(
            "neighborhood", {"city_id": self.major_city.pk, "neighborhood_id": self.pk}
        )

    def api_url(self):
        return url_reverser(
            "neighborhood_api",
            {"city_id": self.major_city.pk, "neighborhood_id": self.pk},
        )

    def ct(self):
        return self.major_city

    def get_name(self):
        return self.name

    def full_name(self) -> str:
        return self.name

    def short_name(self) -> str:
        return self.name

    def city_q(self) -> Q:
        return Q(nstneighborhood=self)

    def neighborhood_q(self) -> Q:
        return Q(pk=self)

    def neighborhood_list(self) -> "QuerySet[NstNeighborhood]":
        return self_as_qs(self)

    def region_q(self) -> Q:
        return Q(neighborhoods=self)

    def ps_q(self) -> Q:
        return Q(nstlocation__neighborhood=self)

    def nest_q(self) -> Q:
        return Q(neighborhood=self)

    def park_list(self) -> "QuerySet[NstLocation]":
        if hasattr(self, "nstlocation_set"):
            return self.nstlocation_set.all()
        return NstLocation.objects.none()

    def s2id(self, level: int = 12) -> CellId:
        return super().s2id(level)


class NstParkSystem(models.Model, HasURLMixin, ComplicatedNameMixin, Place):
    name = models.CharField(max_length=123)
    website = models.CharField(max_length=234, blank=True, null=True)

    class Meta:
        db_table = "nst_park_system"

    def __str__(self):
        return f"{self.name} [{self.pk}]"

    def web_url(self):
        return url_reverser("park_sys", {"ps_id": self.pk})

    def api_url(self):
        return url_reverser("ps_api", {"ps_id": self.pk})

    def get_name(self):
        return self.name

    def short_name(self):
        return self.name

    def full_name(self):
        return self.name

    def city_q(self) -> Q:
        return Q(nstneighborhood__nstlocation__park_system=self)

    def neighborhood_q(self) -> Q:
        return Q(nstlocation__park_system=self)

    def region_q(self) -> Q:
        return Q(neighborhoods__nstlocation__park_system=self)

    def ps_q(self) -> Q:
        return Q(pk=self)

    def park_system_list(self) -> "QuerySet[NstParkSystem]":
        return self_as_qs(self)

    def nest_q(self) -> Q:
        return Q(park_system=self)

    def park_list(self) -> "QuerySet[NstLocation]":
        if hasattr(self, "nstlocation_set"):
            return self.nstlocation_set.all()
        return NstLocation.objects.none()


class NstRotationDate(models.Model, Place):
    """
    Place is subclassed here for the abstract methods
    (and also because it's a place in time)
    """

    num = models.AutoField(primary_key=True)
    date = models.DateTimeField()
    special_note = models.CharField(max_length=123, blank=True, null=True)
    date_list = models.ManyToManyField(
        "NstLocation", through="NstSpeciesListArchive", symmetrical=True
    )

    class Meta:
        db_table = "nst_rotation_dates"

    def __str__(self):
        return f"{self.num} [{str(self.date).split(' ')[0]}]"

    def __cmp__(self, other):
        return self.date.__cmp__(other.date)

    def __lt__(self, other):
        return self.date < other.date

    def date_priority_display(self) -> str:
        return f"{self.date.strftime('%Y-%m-%d')} (rotation {self.num})"

    def city_q(self) -> Q:
        return Q(neighborhoods__nests__rotations=self)

    def neighborhood_q(self) -> Q:
        return Q(nests__rotations=self)

    def region_q(self) -> Q:
        return Q(neighborhoods__nests__rotations=self)

    def ps_q(self) -> Q:
        return Q(nests__rotations=self)

    def nest_q(self) -> Q:
        return Q(rotations=self)

    def active_rotations(self) -> "QuerySet[NstRotationDate]":
        return self_as_qs(self)


class NstSpeciesListArchive(models.Model):
    rotation_num = models.ForeignKey(
        NstRotationDate, models.DO_NOTHING, db_column="rotation_num"
    )
    nestid = models.ForeignKey(NstLocation, models.DO_NOTHING, db_column="nestid")
    species_txt = models.CharField(max_length=111, blank=True, null=True)
    species_no = models.IntegerField(db_column="species_no", blank=True, null=True)
    confirmation = models.BooleanField(blank=True, null=True, default=False)
    id = models.AutoField(primary_key=True, db_column="django_sequence_id")
    special_notes = models.CharField(max_length=111, blank=True, null=True)
    species_name_fk = models.ForeignKey(
        "speciesinfo.Pokemon",
        models.DO_NOTHING,
        db_column="django_pkmn_key",
        to_field="name",
        null=True,
        blank=True,
    )
    last_mod_by = models.ForeignKey(
        NstAdminEmail, models.SET_NULL, db_column="last_mod_by", null=True
    )

    class Meta:
        db_table = "nst_species_list_archive"
        unique_together = (("rotation_num", "nestid"),)

    def __str__(self):
        return f"{self.species_txt} at {self.nestid.get_name()} [{self.nestid.nestID}] \
on {self.rotation_num.date_priority_display()}"

    def __cmp__(self, other):
        if self.rotation_num < other.rotation_num:
            return -1
        if self.rotation_num > other.rotation_num:
            return 1
        if self.nestid < other.nestid:
            return -1
        if self.nestid > other.nestid:
            return 1
        return 0  # should not happen

    def __lt__(self, other):
        if self.rotation_num < other.rotation_num:
            return True
        if self.rotation_num > other.rotation_num:
            return False
        if self.nestid < other.nestid:
            return True
        return False

    def sp_no(self) -> Optional[str]:
        return None if self.species_no is None else f"{self.species_no:03}"


class AirtableImportLog(models.Model):
    time = models.DateTimeField(null=True)
    city = models.CharField(null=True, max_length=25)
    end_num = models.IntegerField(null=True)
    first_reports = models.IntegerField(null=True)
    confirmations = models.IntegerField(null=True)
    conflicts = models.IntegerField(null=True)
    errors = models.IntegerField(null=True)
    duplicates = models.IntegerField(null=True)
    total_import_count = models.IntegerField(null=True)

    class Meta:
        db_table = "airtable_import_log"


class NstRawRpt(models.Model, HasCityMixin, HasURLMixin):
    nsla_pk = models.ForeignKey(
        NstSpeciesListArchive,
        models.SET_NULL,
        null=True,
        db_column="nsla_pk",
        related_name="report_audit",
    )
    bot = models.ForeignKey(NstAdminEmail, models.SET_NULL, null=True)
    user_name = models.CharField(max_length=120, blank=False, null=True)
    server_name = models.CharField(max_length=120, null=True, blank=True)
    nsla_pk_unlink = models.IntegerField(default=0)
    timestamp = models.DateTimeField(null=True)
    foreign_db_row_num = models.IntegerField(null=True)
    raw_species_num = models.CharField(
        max_length=120, null=True
    )  # legacy naming scheme, as this is not an Int field anymore
    attempted_dex_num = models.ForeignKey(
        "speciesinfo.Pokemon", models.SET_NULL, null=True
    )  # Needs to be Int and not FK to play well with Django
    raw_park_info = models.CharField(max_length=120, null=True, blank=True)
    parklink = models.ForeignKey(NstLocation, models.SET_NULL, null=True)
    action = models.IntegerField(null=True)
    calculated_rotation = models.ForeignKey(NstRotationDate, models.SET_NULL, null=True)

    class Meta:
        db_table = "nst_raw_rpt"

    def __str__(self) -> str:
        return f"{self.user_name} reported {self.raw_species_num} at {self.raw_park_info} on {self.timestamp}"

    def privacy_str(self) -> str:
        return f"{self.raw_species_num} reported at {self.raw_park_info} on {self.timestamp}"

    def web_str(self) -> (datetime, str):
        hsh = hash(self.user_name.lower())
        offset = -int(str(hsh)[-1])
        return self.timestamp, self.raw_species_num, hex(hsh)[offset - 5 : offset - 1]

    def web_url(self):
        return url_reverser(
            "nest_history",
            {"city_id": self.nsla_pk.nestid.ct(), "nest_id": self.nsla_pk.nestid.pk},
        )

    def api_url(self):
        return url_reverser("", {})

    def ct(self):
        return self.bot.city


"""
^^^ Classes and Models

vvv Methods
"""


def get_rotation(date) -> NstRotationDate:
    """
    Returns a NstRotation object
    :param date: some form of date or rotation number (either int or str)
    :return: NstRotation object on or before the specified date
    """
    date = str(date).strip()  # handle both str and int input
    if len(date) < 4 and str_int(date):
        try:  # using the input as a direct rotation number
            return NstRotationDate.objects.get(pk=int(date))
        except NstRotationDate.DoesNotExist:
            return get_rotation("t")  # default to today if it's junk
    date = parse_date(date)  # parse the date
    return NstRotationDate.objects.filter(date__lte=date).order_by("-date")[0]


def query_nests(
    search: Union[str, int],
    location_id: Optional[Union[Place, int]] = None,
    location_type: str = "",
    only_one: bool = False,
    exclude_permanent: bool = True,
    restrict_city: Optional[Union[NstMetropolisMajor, int]] = None,
    input_set: "Optional[QuerySet[NstLocation]]" = NstLocation.objects.all(),
) -> "QuerySet[NstLocation]":
    """
    Queries nests that match a given name

    To return all nests in an area, set search to ""

    To enforce a single result, set only_one to True and then .get() on the result
    Yosemite = query_nests("Yosemite", only_one=True).get()

    :param search: name to match on nest, set to "" to match all nests
    :param location_id: id of the location to search
    :param location_type: "city", "neighborhood", or "region" (only required for integer location_ids)
    :param only_one: throw an error if more than one result
    :param exclude_permanent: exclude nests with permanent nesting species from the results
    :param restrict_city: enforce that the nest results have some tangential relationship to this city
                          this isn't sensible without location_id being specified
    :param input_set: start with a restricted set rather than all NstLocation entries
    :return: A QuerySet of NstLocation results
    """
    name: Q = Q(nestID=search) if only_one and str_int(search) else (
        Q(official_name__icontains=search)
        | Q(nestID=search if str_int(search) else None)  # handle 18th street library
        | Q(short_name__icontains=search)
        | Q(alternate_name__name__icontains=search)
    )
    removals: Q = Q(permanent_species__isnull=False) if exclude_permanent else Q()
    place: Q = Q()
    if isinstance(location_id, int):
        location_type = str(location_type).strip().lower() if location_type else None
        place |= {  # legacy code for being passed ints
            "city": Q(neighborhood__major_city=location_id),
            "neighborhood": Q(neighborhood=location_id),
            "region": Q(neighborhood__region=location_id),
            "ps": Q(park_system=location_id),
        }.get(location_type, Q())
    elif isinstance(location_id, Place):
        place |= Q(pk__in=location_id.park_list())
    city: Q = Q(
        Q(neighborhood__major_city=restrict_city)
        | Q(neighborhood__region__neighborhoods__major_city=restrict_city)
    ) if restrict_city else Q()
    return (
        input_set.filter(name & place & city)
        .exclude(removals)
        .distinct()
        .order_by(Lower("official_name"))
    )


class ReportStatus(NamedTuple):
    """
    Status of the report
        0 duplicate [no action]
        1 first report
        2 confirmation
        4 conflict
        6 deletion
        7 non-bot overwrite (always successful)
        9 error

    Errors should always have something in the type & location fields.
    """

    row: Optional[NstRawRpt]
    status: int
    errors_by_code: Optional[Dict[int, Tuple[str, str, str]]]
    errors_by_location: Optional[Dict[str, Tuple[int, str, str]]]


def add_a_report(
    name: str,
    nest: Union[int, str],
    timestamp: datetime,
    species: Union[int, str],
    bot_id: int,
    server: Optional[str] = None,
    rotation: Optional[NstRotationDate] = None,
    confirmation: Optional[bool] = None,
    search_all: bool = False,
    subsearch_place: Optional[int] = None,
    subsearch_type: str = "city",
) -> ReportStatus:
    """
    Adds a raw report and updates the NSLA if applicable
    This thing is **long** and full of ugly business logic

    For "bots" with an is_bot != 1, reports always succeed at updating
    non-bot "bots" do not generate a NstRawReport entry if they do not modify anything

    :param subsearch_type: "city"/"region"/"neighborhood" specifies which model to use on query_nests
    :param subsearch_place: numeric id of the above
    :param search_all: search for all species or just the currently nestable ones
    :param confirmation: leave None to let the system decide how to handle this
    :param name: who submitted the report
    :param server: server identifier
    :param nest: ID of nest, assumed to be unique
    :param timestamp: timestamp of report
    :param species: string or int of the species, assumed to be unique
    :param bot_id: bot ID
    :param rotation: pre-calculated rotation number
    :return: (see ReportStatus docstring)
    """

    def handle_validation_errors() -> ReportStatus:
        """Handles on reporting on multiple errors"""
        by_code: dict = {}
        for location in error_list.keys():
            code, text, bad_value = error_list[location]
            by_code[code] = (location, text, bad_value)

        return ReportStatus(None, 9, by_code, error_list)

    def record_report(status: int) -> ReportStatus:
        """Shoves the report into NstRawRpt with appropriate links"""
        rpt = NstRawRpt.objects.create(
            action=status,
            attempted_dex_num=sp_lnk,
            bot=bot,
            calculated_rotation=rotation,
            nsla_pk=nsla_link,
            nsla_pk_unlink=nsla_link.pk,
            raw_park_info=nest,
            raw_species_num=species,
            timestamp=timestamp,
            user_name=name,
            server_name=server,
            parklink=park_link,
        )
        return ReportStatus(rpt, status, None, None)

    def update_nsla(status_code: int) -> ReportStatus:
        """Updates the NSLA and leaves"""
        nsla_link.confirmation = confirmation
        nsla_link.species_name_fk = sp_lnk
        nsla_link.species_no = sp_lnk.dex_number if sp_lnk else None
        nsla_link.species_txt = sp_lnk.name if sp_lnk else species
        nsla_link.last_mod_by = bot
        nsla_link.save()
        return record_report(status_code)

    #
    # setup & validate internal variables from input
    #
    error_list: Dict[str, Tuple[int, str, str]] = {}
    name = name.strip()
    if not name:
        error_list["user_name"] = (417, "No name given", "")
    if not timestamp:
        error_list["timestamp"] = (416, "Timestamp is emtpy", "")
    try:  # bot id
        bot: Optional[NstAdminEmail] = NstAdminEmail.objects.get(pk=bot_id)
    except NstAdminEmail.DoesNotExist:
        error_list["bot_id"] = (401, "Bad bot ID", f"{bot_id}")
        bot = None
    restricted: bool = bot.restricted() if bot else True
    try:  # species link
        sp_lnk: Optional[Pokemon] = match_species_by_name_or_number(
            species,
            only_one=True,
            input_set=Pokemon.objects.all()
            if search_all
            else enabled_in_pogo(nestable_species()),
            age_up=True,
            previous_evolution_search=True,
        ).get()
    except Pokemon.DoesNotExist:
        if restricted:
            error_list["pokémon"] = (404, "not found", f"{species}")
        sp_lnk = None  # free-text pokémon entries
    except Pokemon.MultipleObjectsReturned:
        if restricted:
            error_list["pokémon"] = (412, "too many results", f"{species}")
        sp_lnk = None  # free-text it for human entries
    try:  # park link
        if not subsearch_place:
            subsearch_place = bot.city.pk if bot.city else None
        park_link: Optional[NstLocation] = get_true_self(
            query_nests(
                nest,
                location_type=subsearch_type,  # could change later for more specific report forms
                location_id=subsearch_place,
                only_one=True,
                exclude_permanent=True if restricted else False,
                restrict_city=bot.city if bot else None,
            ).get()
        )
    except NstLocation.MultipleObjectsReturned:
        error_list["nest"] = (412, "too many results", f"{nest}")
        park_link = None
    except NstLocation.DoesNotExist:
        error_list["nest"] = (404, "not found", f"{nest}")
        park_link = None
    if rotation is None:  # rotation
        try:
            rotation = get_rotation(timestamp)
        except ValueError:
            error_list["timestamp"] = (417, "Invalid timestamp", f"{timestamp}")
        except NstRotationDate.DoesNotExist:
            error_list["timestamp"] = (404, "no rotation found", f"{timestamp}")
    if error_list:
        # this could be higher for marginal performance gain in a high-write environment
        return handle_validation_errors()

    #
    # check for prior art and create NSLA row if none exists
    #
    nsla_link, fresh = NstSpeciesListArchive.objects.get_or_create(
        rotation_num=rotation,
        nestid=park_link,  # if this is None, it would have errored already
        defaults={
            "confirmation": confirmation,
            "species_name_fk": sp_lnk,
            "species_no": sp_lnk.dex_number if sp_lnk else None,
            "species_txt": sp_lnk.name if sp_lnk else species,
            "last_mod_by": bot,
        },
    )
    if fresh:  # we're done if it's a new report
        return record_report(2 if confirmation else 1)

    # duplicate-checking and conflict resolution
    prior_reports: "QuerySet[NstRawRpt]" = NstRawRpt.objects.filter(
        Q(nsla_pk=nsla_link) | Q(nsla_pk_unlink=nsla_link.pk)
    ).order_by("-timestamp")

    # no change from manual edit
    if (
        nsla_link.species_name_fk == sp_lnk
        and bool(nsla_link.confirmation) == bool(confirmation)
        and not restricted
    ):
        return ReportStatus(None, 0, None, None)
    # force change from manual edit
    if not restricted:
        return update_nsla(7)
    # it's only bot posting from here on

    if sp_lnk == nsla_link.species_name_fk:  # confirmations and duplicates
        if prior_reports.filter(
            user_name__iexact=name, attempted_dex_num=sp_lnk
        ).count():
            return record_report(0)  # exact duplicates
        if nsla_link.confirmation:
            return record_report(2)  # previously-confirmed nests
        confirmation = True  # freshly-confirmed reports
        return update_nsla(2)

    #
    # conflicted nests should be all that's left by now
    #

    # only take one report to update to the next species
    # unless it's confirmed by a human or system bot
    if sp_lnk in get_surrounding_species(
        nsla_link.species_name_fk, nestable_species()
    ).values() and (nsla_link.last_mod_by.restricted() or not nsla_link.confirmation):
        confirmation = False
        return update_nsla(1)
    # human and bot confirmations need to go through the normal double agreement to overturn process

    # count the nests from this rotation, then select the nest that most recently has two reports that agree
    # this assumes that the report being added is always the most recent one (so it may break on historic data import)
    if prior_reports.filter(attempted_dex_num=sp_lnk).count():
        # there was a prior report for this nest that agrees with the species given here
        confirmation = True if nsla_link.last_mod_by.restricted() else False
        return update_nsla(2)

    # update if the same user reports the nest again with better data
    if (
        prior_reports.first() is not None
        and prior_reports.first().user_name.lower() == name.lower()
    ):  # preserve case when saving but ignore it for comparison
        confirmation = False
        return update_nsla(1)

    # anything from here on is a conflict that can't get updated
    if prior_reports.exclude(attempted_dex_num=sp_lnk).count():
        return record_report(4)

    # always return something, even if I screwed up the logic elsewhere
    error_list["unknown"] = (
        500,
        "Something got missed",
        "nestlist.models.add_a_report",
    )
    return handle_validation_errors()


def nsla_sp_filter(
    species: Union[str, int],
    nsla: "QuerySet[NstSpeciesListArchive]" = NstSpeciesListArchive.objects.all(),
    species_set: "Optional[QuerySet[Pokemon]]" = None,
    single_species: bool = False,
) -> "QuerySet[NstSpeciesListArchive]":
    if not species_set:  # putting this as a default param raises error
        species_set = enabled_in_pogo(nestable_species())
    return nsla.filter(
        Q(
            species_name_fk__in=match_species_by_name_or_number(
                sp_txt=species,
                previous_evolution_search=True,
                age_up=True,
                input_set=species_set,
                only_one=single_species,
            )
        )
        | Q(species_txt__icontains=species)  # for free-text row-matching
    )


def get_local_nsla_for_rotation(
    rotation: NstRotationDate,
    location_pk: Union[int, Place],
    location_type: str = "",
    species: Optional[str] = None,
) -> "QuerySet[NstSpeciesListArchive]":
    """
    :param rotation: NstRotationDate object
    :param location_pk: numeric ID of location to filter (or pure object)
    :param location_type: 'city', 'neighborhood', or 'region'
    :param species: optional filter for species
    :return: The filtered NSLA for the given location and date
    """
    out_list: "QuerySet[NstSpeciesListArchive]" = NstSpeciesListArchive.objects.filter(
        rotation_num=rotation,
        nestid__in=query_nests(
            "",
            location_type=location_type,
            location_id=location_pk,
            exclude_permanent=False,
        ),
    ).order_by("nestid__official_name")
    return nsla_sp_filter(species, out_list) if species else out_list


def collect_empties(
    search_type: Union[Type, str],
    rotation: Optional[NstRotationDate] = None,
    location: Optional[Place] = None,
) -> QuerySet:
    """
    Collects all the empties (as defined by no NSLA entries)
    :param search_type: which type of location to return the empty for
    :param rotation: empties for a specific rotation
    :param location: restrict to a location
    :return: the empty places (for that rotation, in that location)
    """

    if isinstance(search_type, str):
        search_type = {
            "park": NstLocation,
            "nest": NstLocation,
            "neighborhood": NstNeighborhood,
            "city": NstMetropolisMajor,
            "region": NstCombinedRegion,
            "ps": NstParkSystem,
            "rotation": NstRotationDate,
            "date": NstRotationDate,
        }.get(search_type.strip().lower())
    assert search_type is not None, f"invalid search_type string passed"

    if search_type == NstRotationDate:
        return (
            NstRotationDate.objects.exclude(pk__in=location.active_rotations())
            if location
            else NstRotationDate.objects.exclude(
                Q(nstspecieslistarchive__in=NstSpeciesListArchive.objects.all())
            )
        )

    nsla_exclude_list: "QuerySet[NstSpeciesListArchive]" = (
        get_local_nsla_for_rotation(rotation, location)
        if rotation
        else NstSpeciesListArchive.objects.all()
    )
    filled_nests: "QuerySet[NstLocation]" = NstLocation.objects.filter(
        nstspecieslistarchive__in=nsla_exclude_list
    )
    exclusions: Q = {
        NstLocation: Q(pk__in=filled_nests),
        NstNeighborhood: Q(nstlocation__in=filled_nests),
        NstMetropolisMajor: Q(nstneighborhood__nstlocation__in=filled_nests),
        NstCombinedRegion: Q(neighborhoods__nstlocation__in=filled_nests),
        NstParkSystem: Q(nstlocation__in=filled_nests),
    }.get(search_type, Q())
    f = None
    if location:
        f = {
            NstLocation: location.park_list,
            NstNeighborhood: location.neighborhood_list,
            NstMetropolisMajor: location.city_list,
            NstCombinedRegion: location.region_list,
            NstParkSystem: location.park_system_list,
        }.get(search_type)
        f = f()
    if f is None:
        f = search_type.objects.all()
    return f.exclude(exclusions)


def collect_empty_nests(
    rotation: Optional[NstRotationDate] = None, location_pk: Optional[Place] = None
) -> "QuerySet[NstLocation]":
    """
    Collect empty nests
    Params function just like get_local_nsla_for_rotation
    What is described below is the behavior when they are None
    :param rotation: returns nests that never have had a report
    :param location_pk: returns from all nests in the system
    :return: a list of nests that don't have a report for the specified location & rotation
    """
    return collect_empties(NstLocation, rotation, location_pk).exclude(
        duplicate_of__isnull=False
    )


def rotations_without_report(
    nest: NstLocation, species: str = ""
) -> "QuerySet[NstRotationDate]":
    """
    Finds rotations without any report for a given nest

    If this is a species-specific search on a nest page, return nothing to avoid giving misleading results
    """
    return (
        NstRotationDate.objects.exclude(nstlocation=nest)
        if not species
        else NstRotationDate.objects.none()
    )


def park_nesting_history(
    nest: NstLocation, species: Optional[str] = None
) -> "QuerySet[NstSpeciesListArchive]":
    return (
        nsla_sp_filter(species, NstSpeciesListArchive.objects.filter(nestid=nest))
        if species
        else NstSpeciesListArchive.objects.filter(nestid=nest)
    ).order_by("-rotation_num")


def species_nesting_history(
    city: "QuerySet[NstLocation]", sp: str
) -> "QuerySet[NstSpeciesListArchive]":
    return nsla_sp_filter(
        sp, NstSpeciesListArchive.objects.filter(nestid__in=city), single_species=True
    ).order_by("-rotation_num")


class NewRotationStatus(NamedTuple):
    rotation: Optional[NstRotationDate]
    success: bool
    note: str


def new_rotation(
    rot8d8time: datetime, rotation_user: int = settings.SYSTEM_BOT_USER
) -> NewRotationStatus:
    """
    Rotates the nests.
    :param rot8d8time: datetime object (with timezone) indicating the new rotation date
    :param rotation_user: user to store in the NstRawRpt log and NSLA
    :return: the NstRotationDate object, a True/False success indicator, and any notes
    """
    if len(NstRotationDate.objects.filter(date__contains=rot8d8time.date())) > 0:
        # don't go for multiple rotations on the same day
        return NewRotationStatus(
            None, False, f"Rotation already exists for {rot8d8time.date()}"
        )

    # generate date to save
    try:
        prev_rot: int = NstRotationDate.objects.latest("num").num
    except NstRotationDate.DoesNotExist:
        prev_rot: int = 0  # allow for initial rotations on blank databases
    new_rot = NstRotationDate.objects.create(date=rot8d8time, num=prev_rot + 1)
    perm_nst = NstLocation.objects.exclude(
        Q(permanent_species__isnull=True) | Q(permanent_species__exact="")
    )
    # insert permanent nests
    for nst in perm_nst:
        add_a_report(
            name="Otto",
            nest=nst.pk,  # no call to get_true_self because the duplicate may indicate an overlapping WB & nest
            timestamp=append_utc(datetime.utcnow()),
            species=nst.permanent_species.split("|")[0],
            bot_id=rotation_user,
            server="localhost",
            rotation=new_rot,
            search_all=True,
            confirmation=True,
        )
    return NewRotationStatus(new_rot, True, f"Added rotation {new_rot}")


def delete_rotation(
    rotation_to_delete: NstRotationDate,  # No, the number of the rotation isn't good enough here
    deletion_user: int = settings.SYSTEM_BOT_USER,
    accept_consequences: bool = true_if_y(
        input(
            f"Deleting a rotation also removes all NSLA entries associated with it. Do you wish to continue?"
        )  # for use in some other admin util
        if __name__ == "__main__"
        else f"no.",
        spell_it=True,
    ),
) -> Optional[NstRawRpt]:
    """
    Deletes an erroneously-entered rotation.
    This is not meant to be used on live production systems,
    but there are some protections given to make sure what you're doing if you've made mistakes.
    It's a p. useful function for testing.
    :returns: the NstRawRpt containing the deletion if it happened or None if it was cancelled
    """

    def deletion_dance() -> NstRawRpt:
        """Deletes the rotation and inserts the audit log"""
        # called here because the DB is set up to forbid the deletion of a rotation with any NSLA rows
        deletion_set.delete()
        info = str(rotation_to_delete)
        rotation_to_delete.delete()
        return NstRawRpt.objects.create(
            action=6,  # deletion
            bot=du,
            user_name="Thanos💯",
            raw_species_num=f"Deleted former rotation #{info}",
            raw_park_info=summary,
            timestamp=append_utc(datetime.utcnow()),
        )

    # Prep work and checking inputs
    if not accept_consequences:
        accept_consequences: bool = true_if_y(
            input(
                f"Deleting a rotation also removes all NSLA entries associated with it. Do you wish to continue?"
            ),
            spell_it=True,
        )  # catch it here for imports
    if not accept_consequences:
        return None
    try:
        du: NstAdminEmail = NstAdminEmail.objects.get(id=deletion_user)
    except NstAdminEmail.DoesNotExist:
        print(
            f"Just who is trying to delete this, anyway?  {deletion_user} is not a real user ID."
        )
        return None
    if du.restricted():
        print(f"User {du} is a restricted bot.  No can do: 401.")
        return None
    if not isinstance(rotation_to_delete, NstRotationDate):
        print(f"{rotation_to_delete} is not a NstRotationDate object.")
        return None

    # Gather what to delete
    deletion_set: "QuerySet[NstSpeciesListArchive]" = NstSpeciesListArchive.objects.filter(
        rotation_num=rotation_to_delete
    )
    deletion_size: int = deletion_set.count()
    if deletion_size == 0:
        summary = f"Rotation {rotation_to_delete.pk} had no nests and was deleted without a fuss"
        return deletion_dance()
    auto_upd8_set: "QuerySet[NstSpeciesListArchive]" = deletion_set.filter(
        nestid__permanent_species__isnull=False
    )
    auto_upd8_count: int = auto_upd8_set.count()
    if deletion_size <= auto_upd8_count:
        summary = f"Only {deletion_size} auto-created entries deleted [out of {auto_upd8_count}]"
        return deletion_dance()

    # Final confirmation check on manually-entered nests
    confirmation_prompt: str = f"{deletion_size - auto_upd8_count} user-recorded nests will be deleted "
    confirmation_prompt += (
        f"in addition to the {auto_upd8_count} automatically-rotating nests."
    )
    confirmation_prompt += f"\nType YES if you wish to continue.\t "
    accept_consequences: bool = true_if_y(
        input(confirmation_prompt), insist_case="UPPER", spell_it=True
    )
    return deletion_dance() if accept_consequences else None


def get_true_self(nest: NstLocation) -> NstLocation:
    """Follows a nest.duplicate_of trail to reveal the canonical current nest"""
    return get_true_self(nest.duplicate_of) if nest.duplicate_of else nest
