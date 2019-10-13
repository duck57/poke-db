from django.db import models
from django.db.models import Q
from nestlist.utils import str_int
from django.db.models.query import QuerySet
from typing import Union, Dict, Optional


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
        return f"{self.pk}: {self.region}"


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
        return f"{self.pk}: {self.name}"


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
        Generation, models.DO_NOTHING, db_column="Generation", blank=True, null=True
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
        Generation, models.DO_NOTHING, db_column="Generation"
    )
    evolved_from = models.IntegerField(
        db_column="evolved_from"
    )  # integer field to fix Django assumptions
    pogo_nerf = models.BooleanField(db_column="PoGoNerf", default=False)
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
        PokeCategory, models.DO_NOTHING, db_column="catnum", blank=True, null=True
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
        BodyPlan, models.DO_NOTHING, db_column="Body_Plan", blank=True, null=True
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

    def is_type(self, t1, t2=None) -> bool:
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


def match_species_by_name_or_number(
    sp_txt: Union[str, int],
    input_set: "QuerySet[Pokemon]" = Pokemon.objects.all(),
    age_up: bool = False,
    previous_evolution_search: bool = False,
    only_one: bool = False,
    loose_search: bool = False,
) -> "QuerySet[Pokemon]":
    """
    If you want only a single result, call this function with only_one = True and .get() after
    Works best in a try/except block
    charmander = match_species_by_name_or_number(4, only_one=True).get()

    :param sp_txt: pokémon name or number to search for
                    if the "name" starts with "start" or is a type or region name, return those species
    :param only_one: set to True to enforce returning only a single pokémon
    :param previous_evolution_search: set True to search for previous evolutions of matching species as well
    :param age_up: set True to search for future evolutions of matching species
    :param input_set: a QuerySet of Pokémon eligible to be results
                    leave me null to search from all Pokémon
    :param loose_search: for species like Abra & Mew, whose names are contained within the name of others
                    set to true to return those; otherwise assumes you exact matches match
    :return: a QuerySet of pokémon matching the input string
    """

    def return_me(tentative_list: "QuerySet[Pokemon]") -> "QuerySet[Pokemon]":
        """Inner function to clean up the result list"""
        return tentative_list.order_by("dex_number").distinct()

    def evo_searches(
        orig_pkmn: "QuerySet[Pokemon]", look_for_pre: bool, look_for_next: bool
    ) -> "QuerySet[Pokemon]":
        """
        :param orig_pkmn: QuerySet assumed to contain a single pokémon
        :param look_for_pre: same as previous_evolution_search from above
        :param look_for_next: same as age_up from above
        :return: sends the resulting QuerySet to return_me
        """

        def find_previous_pokemon(
            search_qset: "QuerySet[Pokemon]", doit: bool
        ) -> "QuerySet[Pokemon]":
            if not doit:
                return search_qset
            return (
                Pokemon.objects.filter(pk__in=search_qset.values("previous_evolution"))
                .exclude(pk="(Egg)")
                .distinct()
                | search_qset.distinct()
            ).distinct()

        p = find_previous_pokemon(
            find_previous_pokemon(orig_pkmn, look_for_pre), look_for_pre
        )
        future = (
            input_set.filter(
                Q(previous_evolution__in=orig_pkmn)
                | Q(previous_evolution__previous_evolution__in=orig_pkmn)
            )
            if look_for_next
            else input_set.none()
        ).distinct()
        return input_set.filter(pk__in=(p | future))

    sp_txt = str(sp_txt).strip().lower()
    if not sp_txt:
        # return nothing if nothing is searched for
        return input_set.none()

    # handle some edge case misspellings
    sp_txt = sp_txt.replace("m2", "mewtwo")
    sp_txt = sp_txt.replace("mew2", "mewtwo")
    sp_txt = sp_txt.replace("mew 2", "mewtwo")
    sp_txt = sp_txt.replace("porygon z", "porygon-z")
    sp_txt = sp_txt.replace("porygonz", "porygon-z")
    sp_txt = sp_txt.replace("porygon 2", "porygon2")
    sp_txt = sp_txt.replace("porygon-2", "porygon2")

    # Handle Abra, Mew, megas, etc…
    exact_name_hit: "QuerySet[Pokemon]" = input_set.none() if loose_search else input_set.filter(
        name__iexact=sp_txt
    )
    if exact_name_hit.count():
        return return_me(exact_name_hit)

    # return starters and their evolutions
    if "start" in sp_txt:
        return return_me(input_set.filter(category__in=[50, 52, 53]))

    # handle numeric queries
    # a search for "2" returns Ivysaur and not Porygon 2
    if str_int(sp_txt):
        me = input_set.filter(dex_number=sp_txt)
        # if you enter a number when looking for a single species, stop here
        # stop if nothing was found, too
        if only_one or not me:
            return return_me(me)
        return return_me(evo_searches(me, previous_evolution_search, age_up))

    # handle short queries
    if len(sp_txt) < 3:
        return return_me(input_set.filter(name__icontains=sp_txt))

    # using this dict as a way to be extensible and comment why these functions get called
    attribute_match: dict = {
        "region": input_set.filter(generation__region__icontains=sp_txt),
        "type": match_species_by_type(sp_txt, input_set),
        "egg group": (
            match_species_by_egg_group(sp_txt[4:], input_set)
            if len(sp_txt) > 7 and sp_txt[:4] == "egg:"
            else input_set.none()
        ),
    }
    # Queries matching a Region, Type, or egg do not get the previous/next evolution searches
    if not all(bool(value) is False for value in attribute_match.values()):
        # There has to be a better way to do this
        # this = join unknown multiple QuerySets from a list
        out = input_set.none()
        for attr in attribute_match.keys():
            out = out | attribute_match[attr]
        return return_me(out)

    # search by name and respect future/past evolution searching
    return return_me(
        input_set.filter(
            pk__in=evo_searches(
                Pokemon.objects.filter(name__icontains=sp_txt),
                previous_evolution_search,
                age_up,
            )
        )
    )


def nestable_species() -> "QuerySet[Pokemon]":
    """Compare to the NestSpecies model in nestlist.models"""
    return (
        Pokemon.objects.filter(previous_evolution__category=6, form="Normal")
        .exclude(category__pk__in=[6, 1, 2, 3, 41, 404, 77, 9999])
        .order_by("dex_number")
    )


def enabled_in_PoGO(
    input_list: "QuerySet[Pokemon]" = Pokemon.objects.all()
) -> "QuerySet[Pokemon]":
    """
    This does not attempt to be fully up-to-date with Niantic's phased species rollouts
    Instead, it's a general overview of the species released that errs inclusive
    """
    return input_list.filter(
        Q(
            generation__in=[
                0,  # Utility species like Commons & Water Biomes
                1,  # Kanto
                2,  # Jhoto
                3,  # Hoenn
                4,  # Sinnoh
                5,  # Unova
                # 6,  # Kalos
                # 7,  # Alola
                8,  # Galar may need special casing for cross-promotions once S&S drop
            ]
        )
        | Q(form="Alola")  # Will become unnecessary once Gen 7 is released
        | Q(dex_number__in=[808, 809])  # Nutto (Meltan) & Melmetal special casing
    ).exclude(
        form__icontains="Mega"
    )  # delete me if megas are ever released


def match_species_by_egg_group(
    target_group: str, input_list: "QuerySet[Pokemon]" = Pokemon.objects.all()
) -> "QuerySet[Pokemon]":
    return input_list.filter(
        Q(egg1__name__icontains=target_group)
        | Q(egg1__stadium2name__icontains=target_group)
        | Q(egg2__name__icontains=target_group)
        | Q(egg2__stadium2name__icontains=target_group)
    ).order_by("dex_number")


def match_species_by_type(
    target_type: str, input_list: "QuerySet[Pokemon]" = Pokemon.objects.all()
) -> "QuerySet[Pokemon]":
    return input_list.filter(
        Q(type1__name__icontains=target_type) | Q(type1__name__icontains=target_type)
    ).order_by("dex_number")


def get_surrounding_species(
    search: Pokemon,
    input_list: "QuerySet[Pokemon]" = Pokemon.objects.all().order_by("dex_number"),
) -> Dict[str, Optional[Pokemon]]:
    """Assumes that the input_list is already ordered by pokédex number"""
    return {
        "previous": input_list.filter(dex_number__lt=search.dex_number).last(),
        "next": input_list.filter(dex_number__gt=search.dex_number).first(),
    }
