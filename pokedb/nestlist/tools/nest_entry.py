#!/usr/bin/env python3.7
# coding=UTF-8
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

import sys
import os
import click

if __name__ == "__main__":
    # Setup environ
    sys.path.append(os.getcwd())
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pokedb.settings")

    # Setup django
    import django

    django.setup()

    # now you can import your ORM models
    from nestlist.models import get_rotation, NstSpeciesListArchive, query_nests
    from nestlist.utils import pick_from_qs, input_with_prefill, getdate
    from speciesinfo.models import match_species_by_name_or_number


def match_species_with_prompts(sptxt):
    """

    :param sptxt: pokémon name or number to search for
    :return: the pokémon that matches the species text
    """

    reslst = match_species_by_name_or_number(sptxt)

    if reslst is None or len(reslst) == 0:
        return None, sptxt, None
    if len(reslst) == 1:
        return reslst[0].dex_number, reslst[0].name, reslst[0]

    choice = pick_from_qs(
        "Index of species (not species number): ", reslst, f"{sptxt} [None]"
    )
    if choice > 0:
        choice -= 1  # deal with the 0 option
        return (reslst[choice].dex_number, reslst[choice].name, reslst[choice])
    return None, sptxt, None


def search_nest_query(search):
    """
    :param search: either a nest ID or a string to search
    :return: a nest
    """

    res = query_nests(search)

    if len(res) == 1:
        return res[0]
    if len(res) == 0:
        print("No nests found")
        return 0

    choice = pick_from_qs(
        "Enter the number of the park you would like to display: ", res, True
    )
    return res[choice - 1] if choice > 0 else 0  # prevent out-of-bound indices


def update_park(rotnum, search=None, species=None):
    """
    TODO: replace the meat of this method with the new method factored out of importairtable
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

    results1 = search_nest_query(search)
    if results1 == 0:
        return False

    print(str(results1))

    cur = None

    try:
        cur = NstSpeciesListArchive.objects.get(nestid=results1, rotation_num=rotnum)
        current = cur.species_txt
        confirm = cur.confirmation
    except NstSpeciesListArchive.DoesNotExist:
        current = "" if species is None else species
        confirm = False

    if confirm is True:
        current += "|1"
    species = input_with_prefill("Species|confirm? ", current).strip()

    conf = True if len(species.split("|")) > 1 else None
    species = species.split("|")[0]

    if species == "":
        if cur is None:  # Nothing currently there, so nothing to delete
            return False
        cur.delete()
        return False

    spnum, species, fk = match_species_with_prompts(species)
    if spnum is None:
        print(f"Using species as a string and not a species number")

    if cur is None:
        NstSpeciesListArchive.objects.create(
            rotation_num=rotnum,
            nestid=results1,
            confirmation=conf,
            species_no=spnum,
            species_txt=species,
            species_name_fk=fk,
        )
    else:
        cur.confirmation = conf
        cur.species_no = spnum
        cur.species_txt = species
        cur.species_name_fk = fk
        cur.last_mod_by = None  # for God user edits
        cur.save()

    print()
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
def main(date="t", park=None, poke=None):
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