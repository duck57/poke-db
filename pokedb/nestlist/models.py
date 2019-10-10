"""
Models for the nest list

After all the class-based models are the static methods for dealing with the models
which will prove useful all over the place.
"""

from .utils import parse_date, str_int
from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from speciesinfo.models import (
    match_species_by_name_or_number,
    Pokemon,
    nestable_species,
)
from typing import Union, Optional, Tuple, NamedTuple, Dict
from datetime import datetime


class NstAdminEmail(models.Model):
    name = models.CharField(max_length=90, blank=True, null=True)
    city = models.ForeignKey(
        "NstMetropolisMajor", models.DO_NOTHING, db_column="city", blank=True, null=True
    )
    shortname = models.CharField(max_length=20, blank=True, null=True)
    e_mail = models.CharField(db_column="e-mail", max_length=90, blank=True, null=True)
    is_bot = models.PositiveSmallIntegerField(null=True)

    class Meta:
        managed = False
        db_table = "nst_admin_email"

    def __str__(self):
        return f"{self.shortname} [{self.pk}] {self.e_mail}"


class NstAltName(models.Model):
    name = models.CharField(max_length=222)
    main_entry = models.ForeignKey(
        "NstLocation", models.DO_NOTHING, db_column="main_entry"
    )
    hide_me = models.BooleanField(db_column="hideme", default=False)
    id = models.AutoField(primary_key=True, db_column="dj_key")

    class Meta:
        managed = False
        db_table = "nst_alt_name"

    def __str__(self):
        if self.hide_me:
            return f"[hidden, id={self.id}]"
        return f"{self.name} [{self.main_entry.get_name()}]"


class NstCombinedRegion(models.Model):
    name = models.CharField(max_length=222)

    class Meta:
        managed = False
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


class NstLocation(models.Model):
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
        blank=True,
        null=True,
    )
    resident_history = models.ManyToManyField(
        "NstRotationDate", through="NstSpeciesListArchive", symmetrical=True
    )

    class Meta:
        managed = False
        db_table = "nst_location"

    def __str__(self):
        return f"{self.official_name} [{self.nestID}] ({self.neighborhood})"

    def get_name(self):
        return (
            self.short_name
            if (self.short_name is not None and self.short_name != "")
            else self.official_name
        )

    def __cmp__(self, other):
        if self.official_name < other.official_name:
            return -1
        if self.official_name > other.official_name:
            return 1
        return 0  # this should not happen

    def __lt__(self, other):
        return self.official_name < other.official_name

    def ct(self):
        return self.neighborhood.major_city


class NstMetropolisMajor(models.Model):
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

    class Meta:
        managed = False
        db_table = "nst_metropolis_major"

    def __str__(self):
        return self.name


class NstNeighborhood(models.Model):
    name = models.CharField(max_length=222)
    region = models.ForeignKey(
        NstCombinedRegion, models.DO_NOTHING, db_column="region", blank=True, null=True
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

    class Meta:
        managed = False
        db_table = "nst_neighborhood"

    def __str__(self):
        return self.name


class NstParkSystem(models.Model):
    name = models.CharField(max_length=123)
    website = models.CharField(max_length=234, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "nst_park_system"

    def __str__(self):
        return self.name


class NstRotationDate(models.Model):
    num = models.AutoField(primary_key=True)
    date = models.DateTimeField()
    special_note = models.CharField(max_length=123, blank=True, null=True)
    date_list = models.ManyToManyField(
        "NstLocation", through="NstSpeciesListArchive", symmetrical=True
    )

    class Meta:
        managed = False
        db_table = "nst_rotation_dates"

    def __str__(self):
        return f"{self.num} [{str(self.date).split(' ')[0]}]"

    def __cmp__(self, other):
        return self.date.__cmp__(other.date)

    def __lt__(self, other):
        return self.date < other.date

    def date_priority_display(self):
        return f"{self.date} (rotation {self.num})"


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
        managed = False
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


class NstRawRpt(models.Model):
    nsla_pk = models.ForeignKey(
        NstSpeciesListArchive, models.SET_NULL, null=True, db_column="nsla_pk"
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

    def __str__(self):
        return f"{self.user_name} reported {self.raw_species_num} at {self.raw_park_info} on {self.timestamp}"

    def privacy_str(self) -> str:
        return f"{self.raw_species_num} reported at {self.raw_park_info} on {self.timestamp}"


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
    location_id: int = None,
    location_type: str = "",
    only_one: bool = False,
) -> "QuerySet[NstLocation]":
    """
    Queries nests that match a given name

    To return all nests in an area, set search to ""

    To enforce a single result, set only_one to True and then .get() on the result
    Yosemite = query_nests("Yosemite", only_one=True).get()

    :param search: name to match on nest, set to "" to match all nests
    :param location_id: id of the location to search
    :param location_type: "city", "neighborhood", or "region"
    :param only_one: throw an error if more than one result
    :return: None if no results
    """
    if only_one and str_int(search):
        res = NstLocation.objects.filter(nestID=search)
        if res:
            return res
    out = (
        NstLocation.objects.filter(
            Q(official_name__icontains=search)
            | Q(
                nestID=search if str_int(search) else None
            )  # handle 18th street library
            | Q(short_name__icontains=search)
            | Q(nstaltname__name__icontains=search)
        )
        .distinct()
        .order_by("official_name")
    )
    if location_id:
        location_type = location_type.strip().lower()
        if location_type == "city":
            out = out.filter(neighborhood__major_city=location_id)
        elif location_type == "neighborhood":
            out = out.filter(neighborhood=location_id)
        elif location_type == "region":
            # TODO: update this once regions are improved
            out = out.filter(neighborhood__region=location_id)
    return out


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
) -> ReportStatus:
    """
    Adds a raw report and updates the NSLA if applicable
    This thing is **long** and full of ugly business logic

    For "bots" with an is_bot != 1, reports always succeed at updating
    non-bot "bots" do not generate a NstRawReport entry if they do not modify anything

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

    #
    # setup & validate internal variables from input
    #
    error_list: Dict[str, Tuple[int, str, str]] = {}
    name = name.strip()
    is_bot = 1
    if not name:
        error_list["user_name"] = (417, "No name given", "")
    if not timestamp:
        error_list["timestamp"] = (416, "Timestamp is emtpy", "")
    try:  # bot id
        bot: NstAdminEmail = NstAdminEmail.objects.get(pk=bot_id)
        is_bot = bot.is_bot
        # God-editor shortcuts: Pikachu|1 or Tyrogue* or Porygon-Z*|2
        force_confirmation: bool = True if is_bot in [
            0,
            2,
        ] and "|" in species else False
    except NstAdminEmail.DoesNotExist:
        error_list["bot_id"] = (401, "Bad bot ID", f"{bot_id}")
    search_all: bool = True if "*" in species else False
    species = species.split("|")[0].split("*")[0]  # handle nest_entry.py God-mode input
    try:  # species link
        sp_lnk: Optional[Pokemon] = match_species_by_name_or_number(
            species,
            only_one=True,
            input_set=Pokemon.objects.all() if search_all else nestable_species(),
        ).get()
    except Pokemon.DoesNotExist:
        if is_bot == 1:
            error_list["pokémon"] = (404, "not found", f"{species}")
        else:
            sp_lnk = None  # free-text pokémon entries
    except Pokemon.MultipleObjectsReturned:
        if is_bot:
            error_list["pokémon"] = (412, "too many results", f"{species}")
        else:
            sp_lnk = None  # free-text it for human entries
    try:  # park link
        park_link: NstLocation = query_nests(
            nest, location_type="city", location_id=bot.city, only_one=True
        ).get()
    except NstLocation.MultipleObjectsReturned:
        error_list["nest"] = (412, "too many results", f"{nest}")
    except NstLocation.DoesNotExist:
        error_list["nest"] = (404, "not found", f"{nest}")
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
            "confirmation": force_confirmation,
            "species_name_fk": sp_lnk,
            "species_no": sp_lnk.dex_number if sp_lnk else None,
            "species_txt": sp_lnk.name if sp_lnk else species,
            "last_mod_by": bot,
        },
    )
    if fresh:  # we're done if it's a new report
        return record_report(2 if force_confirmation else 1)
    prior_reports: "QuerySet[NstRawRpt]" = NstRawRpt.objects.filter(
        Q(nsla_pk=nsla_link) | Q(nsla_pk_unlink=nsla_link.pk)
    ).order_by("-timestamp")

    # no change from manual edit
    if (
        nsla_link.species_name_fk == sp_lnk
        and nsla_link.confirmation == force_confirmation
        and bot.is_bot != 1
    ):
        return ReportStatus(None, 0, None, None)
    # force change from manual edit
    if bot.is_bot != 1:
        nsla_link.confirmation = force_confirmation
        nsla_link.species_name_fk = sp_lnk
        nsla_link.species_no = sp_lnk.dex_number if sp_lnk else None
        nsla_link.species_txt = sp_lnk.name if sp_lnk else species
        nsla_link.last_mod_by = bot
        nsla_link.save()
        return record_report(7)
    # it's only bot posting from here on

    if sp_lnk == nsla_link.species_name_fk:  # confirmations and duplicates
        if prior_reports.filter(user_name=name, attempted_dex_num=sp_lnk):
            return record_report(0)  # exact duplicates
        if nsla_link.confirmation:
            return record_report(2)  # previously-confirmed nests
        nsla_link.update(confirmation=True)
        return record_report(2)

    #
    # conflicted nests should be all that's left by now
    #

    # if it was edited by a God-mode user, just skip it and move on
    # similarly for humans and the system
    # it's just conflicted nests left by a bot now

    # count the nests from this rotation, then select the nest that most recently has two reports that agree
    # this assumes that the report being added is always the most recent one (so it may break on historic data import)
    conf_check = NstRawRpt.objects.filter(
        calculated_rotation=rotation, parklink=park_link, attempted_dex_num=sp_lnk
    ).order_by("-timestamp")

    # if it's conflicted single reports, the first one wins

    # unless they're both by the same user
    namelist = set()
    namelist.add(name)
    for raw in NstRawRpt.objects.filter(rotation=rotation, parklink=park_link).order_by(
        "-timestamp"
    ):
        namelist.add(raw.name)
    if len(namelist) == 1:
        # then update their initial report
        pass


def get_local_nsla_for_rotation(
    rotation: NstRotationDate, location_pk: int, location_type: str, species: str = None
) -> "QuerySet[NstSpeciesListArchive]":
    """
    :param rotation: NstRotationDate object
    :param location_pk: numeric ID of location to filter
    :param location_type: 'city', 'neighborhood', or 'region'
    :param species: optional filter for species
    :return: The filtered NSLA for the given location and date
    """
    out_list = NstSpeciesListArchive.objects.filter(rotation_num=rotation).order_by(
        "nestid__official_name"
    )
    if species:
        out_list = out_list.filter(
            Q(
                species_name_fk__in=match_species_by_name_or_number(
                    sp_txt=species, previous_evolution_search=True
                )
            )
            | Q(species_txt__icontains=species)  # for free-text row-matching
        )
    if location_type.lower() == "city":
        return out_list.filter(nestid__neighborhood__major_city=location_pk)
    if location_type.lower() == "neighborhood":
        return out_list.filter(nestid__neighborhood=location_pk)
    if location_type.lower() == "region":
        return out_list.filter(nestid__neighborhood__region=location_pk)
    return None
