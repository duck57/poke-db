from django.db import models


# Create your models here.
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
        "nestlist.NstSpeciesListArchive",
        models.SET_NULL,
        null=True,
        db_column="nsla_pk",
    )
    bot = models.ForeignKey("nestlist.NstAdminEmail", models.SET_NULL, null=True)
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
    parklink = models.ForeignKey("nestlist.NstLocation", models.SET_NULL, null=True)
    action = models.IntegerField(null=True)
    dedupe_sig = models.CharField(null=True, blank=False, max_length=50)
    calculated_rotation = models.ForeignKey(
        "nestlist.NstRotationDate", models.SET_NULL, null=True
    )

    class Meta:
        db_table = "nst_raw_rpt"

    def __str__(self):
        return f"{self.dedupe_sig} {self.raw_species_txt}{self.raw_species_num}"
