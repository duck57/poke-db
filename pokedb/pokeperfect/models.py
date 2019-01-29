from django.db import models
from speciesinfo.models import Pokemon, PokeCategory, Type

# Create your models here.


class GoIvFloor(models.Model):
    min = models.AutoField(primary_key=True)
    comment = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'GO_IV_floors'


class GoPowerupLevel(models.Model):
    level = models.DecimalField(db_column='Level', primary_key=True, max_digits=3, decimal_places=1)
    cp_multiplier = models.DecimalField(db_column='CP_Multiplier', max_digits=11, decimal_places=10)
    wild = models.CharField(db_column='Wild', max_length=1)
    total_candy = models.IntegerField()
    total_dust = models.IntegerField()
    next_level_candy = models.IntegerField(blank=True, null=True)
    next_level_dust = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'GO_powerup_level'


class GoTrainerLevel(models.Model):
    level = models.IntegerField(db_column='Level', primary_key=True)
    xp_required = models.IntegerField(db_column='XP_required')
    total_xp = models.IntegerField(db_column='Total_XP', unique=True)
    unlocked_items = models.CharField(db_column='Unlocked_items', max_length=22, blank=True, null=True)
    ball = models.CharField(db_column='Ball', max_length=5, blank=True, null=True)
    balls = models.IntegerField(db_column='Balls', blank=True, null=True)
    potion = models.CharField(db_column='Potion', max_length=6, blank=True, null=True)
    potions = models.IntegerField(db_column='Potions', blank=True, null=True)
    max = models.BooleanField(db_column='Max', max_length=2, blank=True, null=True)
    revives = models.IntegerField(db_column='Revives', blank=True, null=True)
    razz_berries = models.IntegerField(db_column='Razz_Berries', blank=True, null=True)
    incense = models.IntegerField(db_column='Incense', blank=True, null=True)
    lucky_eggs = models.IntegerField(db_column='Lucky_Eggs', blank=True, null=True)
    incubators = models.IntegerField(db_column='Incubators', blank=True, null=True)
    lure_modules = models.IntegerField(db_column='Lure_Modules', blank=True, null=True)
    log_xp = models.DecimalField(db_column='log_XP', max_digits=4, decimal_places=3, blank=True, null=True)
    log_total_xp = models.DecimalField(db_column='log_total_XP', max_digits=4, decimal_places=3, blank=True, null=True)
    max_xp = models.IntegerField(db_column='max_XP', blank=True, null=True)
    nanab_berries = models.IntegerField(db_column='Nanab_Berries', blank=True, null=True)
    pinap_berries = models.IntegerField(db_column='Pinap_Berries', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'GO_trainer_level'


class PogoTeam(models.Model):
    name = models.CharField(unique=True, max_length=11, blank=True, null=True)
    color = models.CharField(max_length=11, blank=True, null=True)
    color_id = models.IntegerField(blank=True, null=True)
    bird = models.ForeignKey('speciesinfo.Pokemon', models.DO_NOTHING, db_column='bird', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'GO_teams'


class GoRaidHp(models.Model):
    level = models.AutoField(primary_key=True)
    hp = models.PositiveIntegerField(db_column='HP')
    time = models.PositiveIntegerField()
    notes = models.CharField(max_length=222, blank=True, null=True)
    min_dps_theory = models.FloatField(blank=True, null=True)
    min_dps_realistic = models.FloatField(blank=True, null=True)
    min_dps_rejoins = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'go_raid_hp'

    def __str__(self):
        return 'T' + str(self.level) + ', ' + str(self.hp) + 'hp'
