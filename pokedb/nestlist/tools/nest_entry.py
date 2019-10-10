#!/usr/bin/env python3.7
# coding=UTF-8
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

"""Module for manual God-mode nest editing"""

import sys
import os
import click
from typing import Union, Optional, Tuple
from datetime import datetime

if __name__ == "__main__":
    # Setup environ
    sys.path.append(os.getcwd())
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pokedb.settings")

    # Setup django
    import django

    django.setup()
    from django.conf import settings

    # now you can import your ORM models
    from nestlist.models import (
        get_rotation,
        NstSpeciesListArchive,
        query_nests,
        NstRotationDate,
        NstLocation,
        add_a_report,
    )
    from speciesinfo.models import (
        match_species_by_name_or_number,
        nestable_species,
        Pokemon,
    )
    from nestlist.utils import pick_from_qs, input_with_prefill, getdate, append_utc


def match_species_with_prompts(
    sptxt: Union[str, int], search_all: bool
) -> Tuple[str, Optional[Pokemon]]:
    """
    :param search_all: restrict to nestable species or not
    :param sptxt: pokémon name or number to search for
    :return: the pokémon that matches the species text
    """

    reslst = match_species_by_name_or_number(
        sptxt.split("*")[0],
        input_set=Pokemon.objects.all() if search_all else nestable_species(),
    )

    if not reslst.count():
        return sptxt, None
    if reslst.count() == 1:
        return reslst[0].name, reslst[0]

    choice = pick_from_qs(
        "Index of species (not species number): ", reslst, f"{sptxt} [None]"
    )
    if choice > 0:
        choice -= 1  # deal with the 0 option
        return reslst[choice].name, reslst[choice]
    return sptxt, None


def search_nest_query(search: Union[int, str]) -> Union[int, NstLocation]:
    """
    :param search: either a nest ID or a string to search
    :return: a nest
    """

    res = query_nests(search)
    num = res.count()

    if num == 1:
        return res[0]
    if num == 0:
        print("No nests found")
        return 0

    choice = pick_from_qs(
        "Enter the number of the park you would like to display: ", res, True
    )
    return res[choice - 1] if choice > 0 else 0  # prevent out-of-bound indices


def update_park(
    rotnum: NstRotationDate, search: Optional[str] = None, species: Optional[str] = None
):
    """
    :param rotnum:
    :param search:
    :param species:
    :return:
    """
    if search is None:
        search = input("Which park do you want to search? ").strip().lower()
    if search == "":
        return 1
    if search == "q":
        return -5
    if search == "?":
        print(
            "Search for parks here.  Leave blank or enter a lowercase q to exit.  ? to display this help again."
        )
        return False

    current_nest = search_nest_query(search)
    if current_nest == 0:
        return False

    print(str(current_nest))

    cur: Union[None, NstSpeciesListArchive] = None
    current: str
    confirm: bool = False

    try:
        cur = NstSpeciesListArchive.objects.get(
            nestid=current_nest, rotation_num=rotnum
        )
        current = cur.species_txt
        confirm = cur.confirmation
    except NstSpeciesListArchive.DoesNotExist:
        current = "" if species is None else species

    if confirm:
        current += "|1"
    species = input_with_prefill("Species|confirm? ", current).strip()

    if species == "":
        if cur is None:  # Nothing currently there, so nothing to delete
            return False
        cur.delete()  # TODO: add some magic to add deletions to the raw report log
        return False

    search_all: bool = True if "*" in species else False
    confirm = True if "|" in species else False
    species = species.split("|")[0].split("*")[0]

    species, fk = match_species_with_prompts(species, search_all)
    if fk is None:
        print(f"Using species as a string and not a species number")

    species += "*" if search_all else ""
    species += "|1" if confirm else ""

    add_a_report(
        name="Manuel",
        nest=current_nest.pk,
        timestamp=append_utc(datetime.utcnow()),
        species=species,
        bot_id=settings.SYSTEM_BOT_USER,
        server="localhost",
        rotation=rotnum,
    )

    print()  # spacing for CLI interface
    return False


@click.command()
@click.option(
    "-d",
    "--date",
    default="today",
    prompt="Date to edit",
    help="Date you choose to edit, can be absolute (YYYY-MM-DD) or relative (w+2)",
)
@click.option("-n", "--park", help="Quick access to park for testing")
@click.option("-s", "--poke", help="Quick pokémon entry for testing")
def main(
    date: str = "t", park: Optional[str] = None, poke: Optional[str] = None
) -> None:
    """
        :param date:
        :param park:
        :param poke:
        :return:
        """
    if date.strip().lower() == "today" or date is None:
        date = "t"
    rot_num = get_rotation(getdate("When were the nests reported? ", date))
    print(f"Editing rotation {rot_num}")
    stop = False
    while stop is False:
        stop = update_park(rot_num, park, poke)
        park, poke = None, None
    print("Goodbye.")
    sys.exit(0)


if __name__ == "__main__":
    main()
