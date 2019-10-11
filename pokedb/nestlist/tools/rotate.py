#!/usr/bin/env python3.7
# coding=UTF-8
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

"""
Script for adding a new rotation.

Currently, rotations do not have an easy undo mechanism, so be careful.
"""

import os
import sys
from datetime import datetime
import pytz
import click

if __name__ == "__main__":
    # Setup environ
    sys.path.append(os.getcwd())
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pokedb.settings")

    # Setup django
    import django
    from django.db.models import Q
    from django.conf import settings

    django.setup()

    # now you can import your ORM models
    from nestlist.models import NstRotationDate, NstLocation, add_a_report
    from nestlist.utils import getdate, local_time_on_date, append_utc


def pacific1pm(dtin: datetime) -> datetime:
    """
    Appends 1pm Pacific to the input date

    The helper function this uses accounts for DST
    :param dtin: date object in
    :return: date object with 13:00 Pacific added
    """
    niatime = pytz.timezone("America/Los_Angeles")
    nia_date = dtin.astimezone(niatime)
    return local_time_on_date(nia_date, 13, niatime, minute=0)


def niantic_event_time(dtin: datetime) -> datetime:
    """In case Niantic changes things on us, edit here"""
    return pacific1pm(dtin)


def decide_rotation_time(rot8d8time: datetime) -> datetime:
    """For choosing the best estimated UTC rotation time"""
    if rot8d8time.microsecond != 0:  # for relative dates in the t+1 form
        # print("Using a live time")
        rot8d8time = rot8d8time.replace(minute=0, second=0, microsecond=0)
        if rot8d8time.weekday() == 3:
            # print("Normal rotation date")
            rot8d8time = rot8d8time.replace(
                hour=0
            )  # normal midnight UTC Thursday migration
        else:
            # 1 PM Pacific, DST-aware
            # print("Abnormal 1 PM Pacific date")
            rot8d8time = niantic_event_time(rot8d8time)
    elif (
        rot8d8time.weekday() != 3 and rot8d8time.hour == 0 and rot8d8time.minute == 0
    ):  # if a future date is passed that is not a Thursday UTC
        rot8d8time = niantic_event_time(rot8d8time)
    return rot8d8time


@click.command()
@click.option(
    "-d",
    "--date",
    default=str(datetime.today().date()),
    prompt="Date of nest shift",
    help="Date when the nest shift occurred, can be absolute (YYYY-MM-DD) or relative (w+2)",
)
# main method
def main(date):
    # date manipulation
    rot8d8time = decide_rotation_time(
        getdate(
            f"What is the date of the nest rotation (blank for today, {datetime.today().date()})? ",
            date.strip(),
        )
    )  # should always be in UTC
    if len(NstRotationDate.objects.filter(date__contains=rot8d8time.date())) > 0:
        print(f"Rotation already exists for {rot8d8time.date()}")
        return  # don't go for multiple rotations on the same day

    # generate date to save
    prev_rot = NstRotationDate.objects.latest("num")
    new_rot = NstRotationDate.objects.create(date=rot8d8time, num=prev_rot.num + 1)
    perm_nst = NstLocation.objects.exclude(
        Q(permanent_species__isnull=True) | Q(permanent_species__exact="")
    )
    for nst in perm_nst:
        # split is to separate the number, + is to mark it confirmed
        psp = nst.permanent_species.split("|")[0] + "|1"
        add_a_report(
            name="Otto",
            nest=nst.pk,
            timestamp=append_utc(datetime.utcnow()),
            species=psp,
            bot_id=settings.SYSTEM_BOT_USER,
            server="localhost",
            rotation=new_rot,
        )
    print(f"Added rotation {new_rot}")


if __name__ == "__main__":
    main()
