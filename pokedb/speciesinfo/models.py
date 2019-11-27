from django.db import models
from django.db.models import Q
from nestlist.utils import str_int
from django.db.models.query import QuerySet
from typing import Union, Dict, Optional, List, Iterable, Any


# Create your models here.


class Biome(models.Model):
    name = models.CharField(max_length=30)
    pogo = models.PositiveIntegerField(db_column="PoGo", blank=True, null=True)

    class Meta:
        db_table = "biome"

    def __str__(self):
        return self.name


class Generation(models.Model):
    region = models.CharField(db_column="Region", max_length=12)
    games = models.CharField(db_column="Games", max_length=111, blank=True, null=True)
    note = models.CharField(db_column="Note", max_length=111, blank=True, null=True)

    class Meta:
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
        db_table = "egg_group"

    def __str__(self):
        return self.name

    def can_breed_with(self, eg2) -> bool:
        if eg2 is None:  # clean data here
            return False
        if self.pk in [0, 15] or eg2.id in [0, 15]:
            return False  # Glitch groups or Undiscovered
        if self.pk == 0 or eg2.id == 0:
            return True  # Dittos
        #  TODO: add filter for Delta ditto during project phase Data Completion
        return True if self.pk == eg2.pk else False


class PokeCategory(models.Model):
    name = models.CharField(unique=True, max_length=22)
    note = models.CharField(max_length=111, blank=True, null=True)

    class Meta:
        db_table = "zc_pkmn_cat"

    def __str__(self):
        return f"{self.pk}: {self.name}"


class BodyPlan(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=69, blank=True, null=True)
    notes = models.CharField(max_length=69, blank=True, null=True)
    alt_name = models.CharField(max_length=50, unique=True, null=True, blank=True)

    class Meta:
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
        db_table = "ability"

    def __str__(self):
        return self.name


class TypeEffectiveness(models.Model):
    otype = models.ForeignKey(
        "Type", models.DO_NOTHING, db_column="otype", related_name="offensive_type"
    )
    relation = models.ForeignKey(
        "TypeEffectivenessRating",
        models.DO_NOTHING,
        db_column="relation",
        blank=True,
        null=True,
    )
    dtype = models.ForeignKey(
        "Type", models.DO_NOTHING, db_column="dtype", related_name="defensive_type"
    )
    id = models.AutoField(db_column="django_id", primary_key=True)

    class Meta:
        db_table = "type_effectiveness"
        unique_together = (("otype", "dtype"),)

    def __str__(self):
        return (
            f"{self.otype.name} {self.relation.description} against {self.dtype.name}"
        )

    search_fields = ["otype", "relation", "dtype"]


class TypeEffectivenessRating(models.Model):
    description = models.CharField(max_length=23)
    dmg_multiplier = models.FloatField()
    pogodamage = models.FloatField(db_column="PoGoDamage")
    oldpogodamage = models.FloatField(db_column="oldPoGoDamage")
    defense_desc = models.CharField(max_length=23, blank=True)

    class Meta:
        db_table = "type_effectiveness_ratings"

    def __str__(self):
        return self.description

    def __cmp__(self, other):
        if self.dmg_multiplier == other.dmg_multiplier:
            return 0
        if self.dmg_multiplier > other.dmg_multiplier:
            return 1
        return -1


class Type(models.Model):
    name = models.CharField(unique=True, max_length=55)
    glitch = models.BooleanField(default=True)
    note = models.CharField(max_length=111, blank=True, null=True)
    weather_boost = models.ForeignKey(
        "GoWeather", models.DO_NOTHING, db_column="weather_boost", blank=True, null=True
    )
    emoji = models.CharField(max_length=8, blank=True, null=True)
    id = models.IntegerField(primary_key=True, db_column="id")
    AtkEffectiveness = models.ManyToManyField(
        "Type",
        symmetrical=False,
        through="TypeEffectiveness",
        through_fields=("otype", "dtype"),
        related_name="attack_effects",
    )

    class Meta:
        db_table = "type_list"

    def __str__(self):
        return self.name

    def matches(self, q) -> bool:
        """
        :param q: query to search
        :return: if q matches either the type's ID or name
        """
        return self.id == q or self.name.lower() == str(q).lower().strip()


class GoWeather(models.Model):
    name = models.CharField(db_column="Name", max_length=20)
    emoji = models.CharField(db_column="Emoji", max_length=8, blank=True, null=True)

    class Meta:
        db_table = "GO_weather"

    def __str__(self):
        return self.emoji


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
        "Generation", models.DO_NOTHING, db_column="Generation", blank=True
    )
    evolved_from = models.IntegerField(
        db_column="evolved_from", default=0
    )  # integer field to fix Django assumptions
    pogo_nerf = models.BooleanField(db_column="PoGoNerf", default=False)
    type1 = models.ForeignKey(
        "Type",
        models.DO_NOTHING,
        db_column="Type1num",
        related_name="primary_type",
        blank=True,
    )
    type2 = models.ForeignKey(
        "Type",
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
        EggGroup,
        models.DO_NOTHING,
        db_column="EG1",
        related_name="egg_group_1",
        blank=True,
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
        "Ability",
        models.DO_NOTHING,
        db_column="Ability1",
        blank=True,
        null=True,
        related_name="main_ability",
    )
    ability2 = models.ForeignKey(
        "Ability",
        models.DO_NOTHING,
        db_column="Ability2",
        blank=True,
        null=True,
        related_name="alternate_ability",
    )
    hidden_ability = models.ForeignKey(
        "Ability",
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

    def can_breed_to(self, input_list: "QuerySet[Pokemon]") -> "QuerySet[Pokemon]":
        if self.egg1 in [0, 15]:  # Undiscovered egg group has no second type
            return input_list.none()
        if self.egg1 == 13:
            return input_list.all()

    def family_root(self):
        return (
            self
            if self.previous_evolution.previous_evolution == self.previous_evolution
            else self.previous_evolution.family_root()
        )

    def other_forms(self):
        return Pokemon.objects.filter(dex_number=self.dex_number).exclude(
            form=self.form
        )

    def prior_stages(self):
        return (
            []
            if self == self.previous_evolution
            else self.previous_evolution.prior_stages().append(self)
        )

    def psqs(self):
        return self_as_qs(self.prior_stages())

    def future_stages(self):
        """Different from evolves_to, as this checks those for future evolutions as well"""
        # It's just a specialized breadth-first non-recursive tree traversal
        out: List[Pokemon] = []
        queue: List[Pokemon] = [self]
        while queue:
            current = queue[0]
            queue = queue[1:]
            out.append(current)
            for p in current.evolves_to.all():
                queue.append(p)
        return out

    def full_lineage(self):
        return self.family_root().future_stages()

    def full_family_tree(self):
        out: List[Pokemon] = self.full_lineage()
        for pkmn in out:
            alts = pkmn.other_forms()
            for alt in alts:
                if alt in out:
                    continue
                parallel_fam = alt.full_lineage()
                for x in parallel_fam:
                    if x in out:
                        continue
                    out.append(x)
        return out


def match_species_by_name_or_number(
    sp_txt: Union[str, int, Pokemon],
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

    if isinstance(sp_txt, Pokemon):
        if not loose_search and not only_one:
            return self_as_qs(sp_txt)
        sp_txt = sp_txt.name

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
    attribute_match: Dict[str, QuerySet[Pokemon]] = {
        "region": input_set.filter(generation__region__icontains=sp_txt),
        "type": match_species_by_type(sp_txt, input_list=input_set),
        "egg group": (
            match_species_by_egg_group(sp_txt[4:], input_set)
            if len(sp_txt) > 7 and sp_txt[:4] == "egg:"
            else input_set.none()
        ),
        "body plan": (
            match_species_by_body_plan(sp_txt[5:], input_set)
            if len(sp_txt) > 8 and sp_txt[:5] == "body:"
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


def enabled_in_pogo(
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
                # 8,  # Galar may need special casing for cross-promotion once S&S drop
            ]
        )
        | Q(form="Alola")  # Will become unnecessary once Gen 7 is released
        | Q(dex_number__in=[808, 809])  # Nutto (Meltan) & Melmetal special casing
    ).exclude(
        Q(form__icontains="Mega")  # delete me if megas are ever released
        | Q(
            category__in=[
                7,  # Mega
                # 9,  # Alternate (leave this off for Altered Giratina)
                77,  # Ultra Beast (remove me once Gen 7 drops)
                9999,  # Glitched Pokémon
            ]
        )
    )


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
    target_type: Union[str, Type],
    *,
    input_list: "QuerySet[Pokemon]" = Pokemon.objects.all(),
    second_type: Union[str, Type, None] = None,
) -> "QuerySet[Pokemon]":
    mono_type: bool = True if isinstance(
        second_type, str
    ) and second_type.lower().strip() in ["none", "mono"] else False
    q1, q2 = Q(), Q()
    if isinstance(target_type, str):
        q1 = Q(type1__name__icontains=target_type)
        q2 = Q(type2__name__icontains=target_type)
    if isinstance(target_type, Type):
        q1 = Q(type1=target_type)
        q2 = Q(type2=target_type)
    if mono_type:
        q2 = Q(type2__isnull=True)
        return input_list.filter(q1 & q2).order_by("dex_number")
    if not second_type:
        return input_list.filter(q1 | q2).order_by("dex_number")
    q3, q4 = Q(), Q()
    if isinstance(second_type, Type):
        q3 = Q(type1=second_type)
        q4 = Q(type2=second_type)
    if isinstance(second_type, str):
        q3 = Q(type1__name__icontains=second_type)
        q4 = Q(type2__name__icontains=second_type)
    return input_list.filter((q1 & q4) | (q2 & q3)).order_by("dex_number")


def match_species_by_body_plan(
    plan: str, input_list: "QuerySet[Pokemon]" = Pokemon.objects.all()
) -> "QuerySet[Pokemon]":
    return input_list.filter(
        Q(body_plan__name__icontains=plan) | Q(body_plan__alt_name__icontains=plan)
    )


def get_surrounding_species(
    search: Pokemon,
    input_list: "QuerySet[Pokemon]" = Pokemon.objects.all().order_by("dex_number"),
) -> Dict[str, Optional[Pokemon]]:
    """Assumes that the input_list is already ordered by pokédex number"""
    return {
        "previous": input_list.filter(dex_number__lt=search.dex_number).last(),
        "next": input_list.filter(dex_number__gt=search.dex_number).first(),
    }


def self_as_qs(
    s: Any, model: "Optional[Type[models.Model]]" = None
) -> "QuerySet[models.Model]":
    """
    Takes the input and returns it wrapped in a QuerySet
    :param s: the thing you want to transform
    :param model: optional specification to stop errors when using potentially-heterogeneous (nested) Iterables
    :return: A QuerySet representation of the input
    """

    # since you can't create a generic empty QuerySet
    generic_empty: QuerySet = model.objects.none() if model else Ability.objects.none()

    if isinstance(s, QuerySet) and not model:  # check inner QS if a model is specified
        return s  # it's already a QuerySet

    if isinstance(s, Iterable):
        # only works if all items are of the same model
        n: QuerySet = generic_empty
        for item in s:
            n = n | self_as_qs(item, model)  # handle nested lists
        return n

    if not s:
        return generic_empty
    if model and not isinstance(s, type(model.objects.all()[0])):
        return generic_empty

    if not hasattr(s, "pk"):
        return generic_empty

    # for future extensibility
    m: Type = type(s)
    n: List = [s.pk]
    return m.objects.filter(pk__in=n)
