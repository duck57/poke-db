#!/usr/bin/env python3
# coding=UTF-8
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

import airtable
import sys
import os
from collections import defaultdict

if __name__ == '__main__':
    # Setup environ
    sys.path.append(os.getcwd())
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pokedb.settings")

    # Setup django
    import django

    django.setup()

    # now you can import your ORM models
    from nestlist.models import NstMetropolisMajor, NstRawRpt, NstRotationDate
    from importairtable.models import AirtableImportLog
    from django.utils import timezone

nested_dict = lambda: defaultdict(nested_dict)


def get_rot8d8(today):
    """
    select the most recent date on or before the supplied date from the database

    this is copied from update.py to make django shut up about a NameError
    :param today: date to check
    :return: rotation corresponding to the most recent one on or before the supplied date
    """

    res = NstRotationDate.objects.filter(date__lte=today).order_by('-num')
    if len(res) > 0:
        return res[0]
    print(f"Date {today} is older than anything in the database.  Using oldest data instead.")

    return NstRotationDate.objects.all().order_by('date')[0]


def get_submission_data_at(city_id, start_num):
    """
    
    :param city_id: 
    :param start_num:
    :return:
    """

    formula_string = 'serial>' + str(start_num)
    return airtable.Airtable(city_id, 'Submissions Data').get_all(formula=formula_string)


def transform_submission_data(at_obj):
    """

    :param at_obj: Airtable object
    :return: nesteddict of the most important attributes for a report to be added to nst_raw_rpt:
        num: serial number from Airtable db; becomes foreign_db_row_num
        species: pokémon species number (extracted from the summary string); becomes raw_species_num
        whodidit: Name field from submission report, used to filter trolls & duplicates; becomes user_name
        park: id of the park, needs to have AT and local db kept in sync; becomes parklink_id and raw_park_info
        sig: method of calculating duplicate reports across servers; becomes dedupe_sig (it's a carrot-delimited string 🥕)
        rotation: rotation number, calculated from the timestamp
    """
    at_tmp = nested_dict()
    for line in at_obj:
        num = line['fields']['serial']
        at_tmp[num]['time'] = line['createdTime']
        at_tmp[num]['rotation'] = get_rot8d8(line['createdTime'].split('T')[0]).num
        at_tmp[num]['species'] = int(str(line['fields']['summary']).split(' ')[0][1:])
        at_tmp[num]['whodidit'] = str(line['fields']['Name']).strip().lower()
        at_tmp[num]['park'] = int(str(line['fields']['summary']).split(' at ')[1].split('.')[0])
        at_tmp[num]['sig'] = str(at_tmp[num]['rotation']) + '🥕' + at_tmp[num]['whodidit'] + '🥕' + str(at_tmp[num]['park'])

    return at_tmp


def __main__():
    for city in NstMetropolisMajor.objects.all():
        # skip improperly configured cities
        if city.airtable_base_id is None or city.airtable_bot_id is None:
            continue

        bot_id = city.airtable_bot_id
        base = city.airtable_base_id
        rpt_start = 0
        rpt_starts = AirtableImportLog.objects.filter(city=base).order_by('-id')
        if len(rpt_starts) > 0:
            rpt_start = rpt_starts[0].end_num

        sub_dat = get_submission_data_at(base, rpt_start)
        tsd_nnl = transform_submission_data(sub_dat)
        print(tsd_nnl)

        if len(tsd_nnl) == 0:
            continue

        AirtableImportLog.objects.create(
                city=base,
                end_num=rpt_start+len(tsd_nnl),
                time=timezone.now()
        )


if __name__ == '__main__':
    __main__()
