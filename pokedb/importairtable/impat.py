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
    from nestlist.models import NstMetropolisMajor


nested_dict = lambda: defaultdict(nested_dict)


def get_submission_data_at(city_id, start_num):
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
        sig: method of calculating duplicate reports across servers; becomes dedupe_sig
    """
    at_tmp = nested_dict()
    for line in at_obj:
        num = line['fields']['serial']
        at_tmp[num]['time'] = line['createdTime']
        at_tmp[num]['species'] = int(str(line['fields']['summary']).split(' ')[0][1:])
        at_tmp[num]['whodidit'] = str(line['fields']['Name']).strip().lower()
        at_tmp[num]['park'] = int(str(line['fields']['summary']).split(' at ')[1].split('.')[0])
        at_tmp[num]['sig'] = str(at_tmp[num]['park']) + at_tmp[num]['whodidit']

    return at_tmp


def __main__():
    for city in NstMetropolisMajor.objects.all():
        if city.airtable_base_id is None:
            continue
        sub_dat = get_submission_data_at(city.airtable_base_id, -82)
        print(transform_submission_data(sub_dat))


if __name__ == '__main__':
    __main__()
