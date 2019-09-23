#!/usr/bin/env python3
# coding=UTF-8
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

import airtable
import sys
import os
import time
from collections import defaultdict

if __name__ == "__main__":
    # Setup environ
    sys.path.append(os.getcwd())
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pokedb.settings")

    # Setup django
    import django

    django.setup()

    # now you can import your ORM models
    from nestlist.models import (
        NstMetropolisMajor,
        NstRotationDate,
        NstLocation,
        NstSpeciesListArchive,
        NstAdminEmail,
        NestSpecies,
        AirtableImportLog,
        NstRawRpt,
    )
    from django.utils import timezone
    from django.db.models import Q
    from speciesinfo.models import Pokemon


# change from a lambda to make PEP8 shut up
def nested_dict():
    return defaultdict(nested_dict)


def get_rot8d8(today):
    """
    select the most recent date on or before the supplied date from the database

    this is copied from update.py to make django shut up about a NameError
    :param today: date to check
    :return: rotation corresponding to the most recent one on or before the supplied date
    """

    res = NstRotationDate.objects.filter(date__lte=today).order_by("-num")
    if len(res) > 0:
        return res[0]
    print(
        f"Date {today} is older than anything in the database.  Using oldest data instead."
    )

    return NstRotationDate.objects.all().order_by("date")[0]


def get_submission_data_at(city_id, start_num):
    """
    
    :param city_id: 
    :param start_num:
    :return:
    """

    formula_string = "serial>" + str(start_num)
    return airtable.Airtable(city_id, "Submissions Data").get_all(
        formula=formula_string
    )


def make_raw_rpt_sig(name, park_id, rot_num):
    return f"{rot_num}🥕{name}🥕{park_id}"


def transform_submission_data(at_obj):
    """

    :param at_obj: Airtable object
    :return: nesteddict of the most important attributes for a report to be added to nst_raw_rpt:
        num: serial number from Airtable db; becomes foreign_db_row_num
        species: pokémon species number (extracted from the summary string); becomes raw_species_num
        whodidit: Name field from submission report, used to filter trolls & duplicates; becomes user_name
        park: id of the park, needs to have AT and local db kept in sync; becomes parklink_id and raw_park_info
        sig: method of calculating duplicate reports across servers; becomes dedupe_sig
            (it's a carrot-delimited string 🥕)
        rotation: rotation number, calculated from the timestamp
    """

    at_tmp = nested_dict()
    for line in at_obj:
        num = line["fields"]["serial"]
        at_tmp[num]["time"] = line["createdTime"]
        at_tmp[num]["rotation"] = get_rot8d8(line["createdTime"].split("T")[0])
        at_tmp[num]["species"] = int(str(line["fields"]["summary"]).split(" ")[0][1:])
        at_tmp[num]["whodidit"] = str(line["fields"]["Name"]).strip().lower()

        # this one below is nasty to deal with standard human-readable Airtable stuff
        at_tmp[num]["park"] = int(
            str(line["fields"]["summary"]).split(" at ")[1].split(".")[0].split('"')[-1]
        )

        at_tmp[num]["sig"] = make_raw_rpt_sig(
            at_tmp[num]["whodidit"], at_tmp[num]["park"], at_tmp[num]["rotation"]
        )
        at_tmp[num]["num"] = num

    return at_tmp


def add_air_rpt(report, bot):
    line_num, status = add_a_report(
        report["whodidit"],
        report["park"],
        report["time"],
        report["species"],
        bot,
        server=f"AirTable#{bot}",
        sig=report["sig"],
        rotation=report["rotation"],
    )

    line_num.foreign_db_row_num = report["num"]
    line_num.save()

    return status


def match_species(sptxt):
    """
    Copied from nest_entry and modified to assume that incoming data is sanitized
    :param sptxt: pokédex number or species name to match
    :return: species number and either a reference to the pokémon or None for an error
    """
    reslst = (
        NestSpecies.objects.filter(
            Q(dex_number=sptxt) | Q(poke_fk__name__icontains=sptxt)
        )
        .order_by("dex_number")
        .distinct()
    )

    if len(reslst) != 1:
        return None
    return reslst[0].dex_number


def match_park(search):
    """
    Copied and modified to error out if not unique
    :param search: either a nest ID or a string to search
    :return: a nest
    """

    res = NstLocation.objects.filter(
        Q(official_name__icontains=search)
        | Q(nestID=search)
        | Q(short_name__icontains=search)  # if/else needed to prevent Value errors
        | Q(nstaltname__name__icontains=search)
    ).distinct()

    if len(res) == 1:
        return res[0]
    elif len(res) == 0:
        return None

    for line in res:
        # check for exact ID matches, in cases like "18th street library" matching both IDs of 1 and 18
        if line.pk == int(search):
            return line

    return None


def mark_action(rpt_row, action):
    rpt_row.action = action
    rpt_row.save()
    return rpt_row, action


def str_int(strin):
    """
    checks if a string will convert to an int
    why isn't this in the standard library?
    :param strin: string to check
    :return: whether the string can convert to an integer
    """

    try:
        int(strin)
    except ValueError:
        return False
    return True


def add_a_report(name, nest, time, species, bot, sig=None, server=None, rotation=None):
    """
    Adds a raw report and updates the NSLA if applicable
    Meant to be generic enough to handle both Discord and Airtable input
    This thing is **long** and full of ugly business logic

    :param name: who submitted the report
    :param server: server identifier
    :param nest: ID of nest, assumed to be unique
    :param time: timestamp of report
    :param species: pokédex number
    :param bot: bot ID
    :param sig: pre-calculated sig, assumed to be correct
    :param rotation: pre-calculated rotation number
    :return: Status of the report
        0 duplicate [no action]
        1 first report
        2 confirmation
        4 conflict
        9 error
    """

    status = 9
    sp_num, sp_txt = None, None
    if str_int(species):
        sp_num = int(species)
    else:
        sp_txt = species
    if rotation is None:
        rotation = get_rot8d8(str(time).split("T")[0])
    if sig is None:
        sig = make_raw_rpt_sig(name, nest, rotation.pk)
    bot = NstAdminEmail.objects.get(pk=bot)
    if bot is None:
        return None, None

    rpt_row = NstRawRpt.objects.create(
        bot=bot,
        user_name=name,
        server_name=server,
        timestamp=time,
        raw_species_num=sp_num,
        raw_species_txt=sp_txt,
        raw_park_info=nest,
        dedupe_sig=sig,
        calculated_rotation=rotation,
    )

    pk_lnk = None
    sp_lnk = match_species(species)
    if sp_lnk is None:
        # error out if species can't be uniquely matched
        # TODO support free-text reports: "Squritle or Bulbasaur", useful for Discord reports
        return mark_action(rpt_row, 9)
    else:
        pk_lnk = Pokemon.objects.get(dex_number=sp_lnk, form="Normal")
        rpt_row.attempted_dex_num = sp_lnk

    parklink = match_park(nest)
    if parklink is None:
        # error out if park can't be uniquely matched
        return mark_action(rpt_row, 9)
    else:
        rpt_row.parklink = parklink

    # sort in reverse-chronological order because we mostly care about the most recent duplicate
    # this might be refactored to its own function one day (or as an internal function)
    # excludes errored and conflicting rows
    dup_check = (
        NstRawRpt.objects.exclude(pk=rpt_row.pk)
        .filter(
            dedupe_sig=sig, action__in=[1, 2, 0]
        )  # count successful reports only during dedupe
        .order_by("-timestamp")
    )
    if len(dup_check) > 0:
        # we only care about the most recent duplicate report
        line = dup_check[0]
        # mark duplicates as duplicate
        if line.attempted_dex_num is not None and line.attempted_dex_num == sp_lnk:
            return mark_action(rpt_row, 0)
        if line.raw_species_num is not None and line.raw_species_num == species:
            return mark_action(rpt_row, 0)
        if line.raw_species_txt is not None and line.raw_species_txt == species:
            return mark_action(rpt_row, 0)

    # check the NSLA for matches
    try:
        nsla_check = NstSpeciesListArchive.objects.get(
            rotation_num=rotation, nestid=parklink
        )
    except NstSpeciesListArchive.DoesNotExist:
        # add new NSLA row, should probably be independent function
        rpt_row.nsla_pk = NstSpeciesListArchive.objects.create(
            rotation_num=rotation,
            nestid=parklink,
            confirmation=False,
            species_name_fk=pk_lnk,
            species_no=sp_lnk,
            species_txt=pk_lnk.name,
            last_mod_by=bot,
        )
        rpt_row.nsla_pk_unlink = rpt_row.nsla_pk.pk
        rpt_row.save()
        return mark_action(rpt_row, 1)

    # confirmations
    if nsla_check.species_name_fk == pk_lnk:
        nsla_check.confirmation = True
        nsla_check.last_mod_by = bot
        nsla_check.save()
        rpt_row.nsla_pk_unlink = nsla_check.pk
        rpt_row.nsla_pk = nsla_check
        rpt_row.save()
        return mark_action(rpt_row, 2)

    # conflicted nests should be all that's left by now
    if nsla_check.last_mod_by is None:
        # if it was edited by a God-mode user, just skip it and move on
        return mark_action(rpt_row, 4)
    if nsla_check.last_mod_by.is_bot != 1:
        # similarly for humans and the system
        return mark_action(rpt_row, 4)
    # it's just conflicted nests left by a bot now

    # count the nests from this rotation, then select the nest that most recently has two reports that agree
    # this assumes that the report being added is always the most recent one (so it may break on historic data import)
    conf_check = NstRawRpt.objects.filter(
        calculated_rotation=rotation, parklink=parklink, attempted_dex_num=sp_lnk
    ).order_by("-timestamp")
    if len(conf_check) > 1:
        nsla_check.confirmation = True
        nsla_check.species_name_fk = pk_lnk
        nsla_check.species_no = sp_lnk
        nsla_check.species_txt = pk_lnk.name
        nsla_check.last_mod_by = bot
        nsla_check.save()
        rpt_row.nsla_pk = nsla_check
        rpt_row.nsla_pk_unlink = nsla_check.pk
        rpt_row.save()
        return mark_action(rpt_row, 2)

    # if it's conflicted single reports, the first one wins

    # unless they're both by the same user
    namelist = set()
    namelist.add(name)
    for raw in NstRawRpt.objects.filter(rotation=rotation, parklink=parklink).order_by(
        "-timestamp"
    ):
        namelist.add(raw.name)
    if len(namelist) == 1:
        # then update their initial report
        nsla_check.confirmation = False
        nsla_check.species_name_fk = pk_lnk
        nsla_check.species_no = sp_lnk
        nsla_check.species_txt = pk_lnk.name
        nsla_check.last_mod_by = bot
        nsla_check.save()
        rpt_row.nsla_pk = nsla_check
        rpt_row.nsla_pk_unlink = nsla_check.pk
        rpt_row.save()
        return mark_action(rpt_row, 1)

    return mark_action(rpt_row, 4)


def import_city(base, bot_id=None):
    rpt_start = 0
    rpt_starts = AirtableImportLog.objects.filter(city=base).order_by("-pk")
    if len(rpt_starts) > 0:
        rpt_start = rpt_starts[0].end_num
    sub_dat = get_submission_data_at(base, rpt_start)
    tsd_nnl = transform_submission_data(sub_dat)
    stats = {0: 0, 1: 0, 2: 0, 4: 0, 9: 0}  # blank stats list

    if len(tsd_nnl) == 0:
        return None
    for rpt in tsd_nnl.keys():
        stats[
            add_air_rpt(tsd_nnl[rpt], bot_id)
        ] += 1  # add/handle the report, then increment the stats counter

    AirtableImportLog.objects.create(
        city=base,
        end_num=rpt_start + len(tsd_nnl),
        time=timezone.now(),
        first_reports=stats[1],
        confirmations=stats[2],
        errors=stats[9],
        conflicts=stats[4],
        duplicates=stats[0],
    )
    return stats


def __main__():
    for city in NstMetropolisMajor.objects.all():
        # skip improperly configured cities
        if city.airtable_base_id is None or city.airtable_bot_id is None:
            continue
        print(
            city.name,
            time.localtime(),
            import_city(city.airtable_base_id, city.airtable_bot_id),
        )
        time.sleep(1)


if __name__ == "__main__":
    __main__()
