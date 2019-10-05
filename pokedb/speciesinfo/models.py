from django.db import models
from django.db.models import Q
from nestlist.utils import str_int

# Create your models here.


class Biome(models.Model):
    name = models.CharField(max_length=30)
    pogo = models.PositiveIntegerField(db_column="PoGo", blank=True, null=True)

    class Meta:
        managed = False
        db_table = "biome"

    def __str__(self):
        return self.name


class Generation(models.Model):
    region = models.CharField(db_column="Region", max_length=12)
    games = models.CharField(db_column="Games", max_length=111, blank=True, null=True)
    note = models.CharField(db_column="Note", max_length=111, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "generations"

    def __str__(self):
        return f"{self.id}: {self.region}"


class EggGroup(models.Model):
    name = models.CharField(max_length=20)
    notes = models.CharField(max_length=199, blank=True, null=True)
    stadium2name = models.CharField(
        db_column="Stadium2name", max_length=20, blank=True, null=True
    )

    class Meta:
        managed = False
        db_table = "egg_group"

    def __str__(self):
        return self.name


class PokeCategory(models.Model):
    name = models.CharField(unique=True, max_length=22)
    note = models.CharField(max_length=111, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "zc_pkmn_cat"

    def __str__(self):
        return self.name


class BodyPlan(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=50, blank=True, null=True)
    notes = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "body_plan"

    def __str__(self):
        return self.name


class Ability(models.Model):
    name = models.CharField(db_column="Name", max_length=50)
    effect = models.CharField(db_column="Effect", max_length=333)
    generation = models.ForeignKey(
        "Generation", models.DO_NOTHING, db_column="Generation", blank=True, null=True
    )
    note = models.CharField(db_column="Note", max_length=99, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "ability"

    def __str__(self):
        return self.name


class Pokemon(models.Model):
    form = models.CharField(max_length=11)
    dex_number = models.IntegerField(db_column="#")
    name = models.CharField(db_column="Name", max_length=255, primary_key=True)
    total = models.IntegerField(db_column="Total", blank=True, null=True)
    hp = models.IntegerField(db_column="HP")
    attack = models.IntegerField(db_column="Attack")
    defense = models.IntegerField(db_column="Defense")
    sp_atk = models.IntegerField(db_column="SpAtk")
    sp_def = models.IntegerField(db_column="SpDef")
    speed = models.IntegerField(db_column="Speed")
    generation = models.ForeignKey(
        "Generation", models.DO_NOTHING, db_column="Generation"
    )
    evolved_from = models.IntegerField(
        db_column="evolved_from"
    )  # integer field to fix Django assumptions
    pogonerf = models.BooleanField(db_column="PoGoNerf", default=False)
    type1 = models.ForeignKey(
        "typeedit.Type",
        models.DO_NOTHING,
        db_column="Type1num",
        related_name="primary_type",
    )
    type2 = models.ForeignKey(
        "typeedit.Type",
        models.DO_NOTHING,
        db_column="Type2num",
        blank=True,
        null=True,
        related_name="alternate_type",
    )
    category = models.ForeignKey(
        "PokeCategory", models.DO_NOTHING, db_column="catnum", blank=True, null=True
    )
    wt_kg = models.FloatField()
    ht_m = models.FloatField()
    egg1 = models.ForeignKey(
        EggGroup, models.DO_NOTHING, db_column="EG1", related_name="egg_group_1"
    )
    egg2 = models.ForeignKey(
        EggGroup,
        models.DO_NOTHING,
        db_column="EG2",
        blank=True,
        null=True,
        related_name="egg_group_2",
    )
    habitat = models.ForeignKey(
        Biome, models.DO_NOTHING, db_column="habitat", blank=True, null=True
    )
    official_color = models.CharField(
        db_column="OfficialColor", max_length=11, blank=True, null=True
    )
    body_plan = models.ForeignKey(
        "BodyPlan", models.DO_NOTHING, db_column="Body_Plan", blank=True, null=True
    )
    description_category = models.CharField(max_length=13, blank=True, null=True)
    ability1 = models.ForeignKey(
        Ability,
        models.DO_NOTHING,
        db_column="Ability1",
        blank=True,
        null=True,
        related_name="main_ability",
    )
    ability2 = models.ForeignKey(
        Ability,
        models.DO_NOTHING,
        db_column="Ability2",
        blank=True,
        null=True,
        related_name="alternate_ability",
    )
    hidden_ability = models.ForeignKey(
        Ability,
        models.DO_NOTHING,
        db_column="HiddenAbility",
        blank=True,
        null=True,
        related_name="hidden_ability",
    )
    nicknames = models.CharField(max_length=88, blank=True, null=True)
    notes = models.CharField(max_length=333, blank=True, null=True)
    nia_cust_hp = models.IntegerField(db_column="NIA_cust_HP", blank=True, null=True)
    nia_cust_atk = models.IntegerField(db_column="NIA_cust_ATK", blank=True, null=True)
    nia_cust_def = models.IntegerField(db_column="NIA_cust_DEF", blank=True, null=True)
    previous_evolution = models.ForeignKey(
        "Pokemon",
        models.SET_NULL,
        related_name="evolves_to",
        null=True,
        db_column="ef_fk_dj",
    )

    class Meta:
        managed = False
        db_table = "pokémon"
        unique_together = (("dex_number", "form"),)

    def __str__(self):
        return f"#{self.dex_number:03} {self.name}"

    def is_type(self, t1, t2=None):
        """
        It is agnostic as to which order the match occurs
        (eg. checking for "Flying, Dragon" on a Dragon/Flying type returns True)

        Accepts strings, ints, or Type objects as t1 and t2
        :param t1: Type to check (required)
        :param t2: Type to check (optional)
        :return: whether the pokémon matches the input type(s)
        """
        if t2 is None:
            return (
                self.type1 == t1
                or self.type2 == t1
                or self.type1.matches(t1)
                or (self.type2 is not None and self.type2.matches(t1))
            )
        return self.is_type(t1) and self.is_type(t2)

    def __cmp__(self, other):
        if self.dex_number == other.dex_number and self.form == other.form:
            return 0
        if self.dex_number < other.dex_number:
            return -1
        if self.dex_number > other.dex_number:
            return 1
        if self.form == "Normal":
            return -1
        if other.form == "Normal":
            return 1
        if self.form < other.form:
            return -1
        return 1


def match_species_by_name_or_number(sp_txt, only_one=False):
    """
    :param sp_txt: pokémon name or number to search for
    :param only_one: set to True to enforce returning only a single pokémon
    :return: a QuerySet of pokémon matching the input string if only_one is False
    otherwise, return the pokémon that matches or raise an exception for multiple matches

    Always returns None for empty lists
    """

    # hardcoded Abra match so it does not match Crabwaler every time
    if str(sp_txt).lower().strip() == "abra":
        res_lst = [Pokemon.objects.get(pk="Abra")]
    else:
        res_lst = (
            Pokemon.objects.filter(
                Q(dex_number=sp_txt if str_int(sp_txt) else None)
                | Q(name__icontains=sp_txt)
            )
            .order_by("dex_number")
            .distinct()
        )
    num_res = len(res_lst)
    if num_res == 0:
        return None
    if only_one:
        if num_res == 1:
            return res_lst[0]
        raise 9 from RuntimeError("Too many results")
    return res_lst
