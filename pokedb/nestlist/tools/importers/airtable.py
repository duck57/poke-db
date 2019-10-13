#!/usr/bin/env python3
# coding=UTF-8
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

"""Import Airtable into the database"""

import os
import sys
import time
from datetime import datetime
from typing import Union, Dict, List
from collections import defaultdict

import airtable

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
        AirtableImportLog,
        add_a_report,
        ReportStatus,
        NstRawRpt,
    )
    from django.utils import timezone
    from nestlist.utils import nested_dict, parse_date


def get_submission_data_at(city_id: str, start_num: Union[str, int]) -> List[Dict]:
    """
    Fetches data from Airtable's servers
    :param city_id: Airtable ID for the table we need
    :param start_num: most recent imported row
    :return: list of new rows
    """
    return airtable.Airtable(city_id, "Submissions Data").get_all(
        formula=f"serial>{start_num}"
    )


def transform_submission_data(at_obj: List[Dict]) -> Dict:
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

    at_tmp: Dict = nested_dict()
    for line in at_obj:
        num: int = line["fields"]["serial"]
        try:
            at_tmp[num]["time"] = parse_date(
                line["createdTime"].split("Z")[0]
            )  # remove Z
        except ValueError:
            at_tmp[num]["time"] = parse_date("March 14, 1592")
        at_tmp[num]["whodidit"] = line["fields"]["Name"].strip().lower()

        try:
            at_tmp[num]["species"] = line["fields"]["summary"].split(" ")[0][1:]
        except ValueError:
            at_tmp[num]["species"] = 69420  # give somethig that will never match
        try:
            at_tmp[num]["park"] = (
                line["fields"]["summary"].split(" at ")[1].split(".")[0].split('"')[-1]
            )  # this is nasty to deal with human-readable Airtable stuff & avoid joins
        except ValueError:
            at_tmp[num]["park"] = 0  # should never match
        at_tmp[num]["num"] = num
    return at_tmp


def add_air_rpt(report: Dict, bot: int):
    output: ReportStatus = add_a_report(
        name=report["whodidit"],
        nest=report["park"],
        timestamp=report["time"],
        species=report["species"],
        bot_id=bot,
        server=f"AirTable#{bot}",
    )  # we don't care about the error list details here, at least for now
    line_num: NstRawRpt = output.row
    status: int = output.status

    if status == 9 or line_num is None:
        print(output, report)
        return 9  # handle errors and move to the next nest

    line_num.foreign_db_row_num = report["num"]
    line_num.save()

    return status


def import_city(base: str, bot_id: int) -> Dict[int, int]:
    """
    Imports from an Airtable base
    """
    try:  # find the most recent record imported to the system
        rpt_start: int = AirtableImportLog.objects.filter(
            city=base, time__isnull=False
        ).latest("time").end_num
    except AirtableImportLog.DoesNotExist:
        rpt_start: int = 0
    tsd_nnl: Dict = transform_submission_data(get_submission_data_at(base, rpt_start))
    stats = defaultdict(lambda: 0)  # empty stats list

    def return_status() -> Dict[int, int]:
        """Magic numbers from nestlist.models.ReportStatus"""
        return {
            0: stats[0],  # duplicates
            1: stats[1],  # new reports
            2: stats[2],  # confirmations
            4: stats[4],  # conflicts
            9: stats[9],  # errors
        }

    if not tsd_nnl:
        return return_status()
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
    )  # only create a new log when successful
    return return_status()


def __main__() -> None:
    for city in NstMetropolisMajor.objects.filter(
        airtable_base_id__isnull=False, airtable_bot_id__isnull=False
    ):
        print(
            city.name,
            datetime.now().isoformat(),
            import_city(city.airtable_base_id, city.airtable_bot_id),
        )
        time.sleep(1)


if __name__ == "__main__":
    __main__()
