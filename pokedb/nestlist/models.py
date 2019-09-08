from django.db import models
from speciesinfo.models import Pokemon
from typeedit.models import Type  # needed to prevent Django from complaining


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
        return f"{self.short_name} [{self.id}] {self.e_mail}"


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
        return f"{self.name} [{self.id}]"

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
    airtable_bot = models.ForeignKey(NstAdminEmail, models.SET_NULL)

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

    def place_name(self):
        if self.region is None:
            return self.name
        else:
            return self.region.name


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
    date = models.DateField(max_length=11)
    special_note = models.CharField(max_length=123, blank=True, null=True)
    date_list = models.ManyToManyField(
        "NstLocation", through="NstSpeciesListArchive", symmetrical=True
    )

    class Meta:
        managed = False
        db_table = "nst_rotation_dates"

    def __str__(self):
        return f"{self.num} [{self.date}]"

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
    city = models.ForeignKey(
        NstMetropolisMajor, models.SET_NULL, db_column="city", null=True
    )
    neighborhood = models.ForeignKey(
        NstNeighborhood, models.SET_NULL, db_column="neighborhood", null=True
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


class NestSpecies(models.Model):
    poke_fk = models.OneToOneField(
        "speciesinfo.Pokemon", models.DO_NOTHING, primary_key=True, db_column="Name"
    )
    dex_number = models.IntegerField(db_column="dex_number", unique=True)
    main_type = models.ForeignKey(
        "typeedit.Type",
        models.DO_NOTHING,
        db_column="Type",
        related_name="nst1type",
        to_field="name",
    )
    subtype = models.ForeignKey(
        "typeedit.Type",
        models.DO_NOTHING,
        to_field="name",
        related_name="nst2type",
        null=True,
        db_column="Subtype",
    )
    generation = models.ForeignKey(
        "speciesinfo.Generation", models.DO_NOTHING, db_column="Generation"
    )

    class Meta:
        managed = False
        db_table = "nest_species_list"

    def __str__(self):
        return str(self.poke_fk)


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
        NstSpeciesListArchive,
        models.SET_NULL,
        null=True,
        db_column="nsla_pk",
    )
    bot = models.ForeignKey(NstAdminEmail, models.SET_NULL, null=True)
    user_name = models.CharField(max_length=120, blank=False, null=True)
    server_name = models.CharField(max_length=120, null=True, blank=True)
    nsla_pk_unlink = models.IntegerField(default=0)
    timestamp = models.DateTimeField(null=True)
    foreign_db_row_num = models.IntegerField(null=True)
    raw_species_num = models.IntegerField(null=True)
    raw_species_txt = models.CharField(max_length=120, null=True)
    attempted_dex_num = models.IntegerField(
        null=True
    )  # Needs to be Int and not FK to play well with Django
    raw_park_info = models.CharField(max_length=120, null=True, blank=True)
    parklink = models.ForeignKey(NstLocation, models.SET_NULL, null=True)
    action = models.IntegerField(null=True)
    dedupe_sig = models.CharField(null=True, blank=False, max_length=50)
    calculated_rotation = models.ForeignKey(
        NstRotationDate, models.SET_NULL, null=True
    )

    class Meta:
        db_table = "nst_raw_rpt"

    def __str__(self):
        return f"{self.dedupe_sig} {self.raw_species_txt}{self.raw_species_num}"
