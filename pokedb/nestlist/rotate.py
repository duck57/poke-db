#!/usr/bin/env python3
# coding=UTF-8
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

import os
import sys
from datetime import datetime

import click
from nestlist.utils import getdate

if __name__ == '__main__':
    # Setup environ
    sys.path.append(os.getcwd())
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pokedb.settings")

    # Setup django
    import django

    django.setup()

    # now you can import your ORM models
    from nestlist.models import NstRotationDate, NstLocation, NstSpeciesListArchive


@click.command()
@click.option(
    '-d',
    '--date',
    default=str(datetime.today().date()),
    prompt="Date of nest shift",
    help="Date when the nest shift occured, can be absolute (YYYY-MM-DD) or relative (w+2)"
)
# main method
def main(date):
    d8 = str(getdate(date.strip()))
    if len(NstRotationDate.objects.filter(date=d8)) > 0:
        print(f"Rotation already exists for {d8}")
        return
    prev_rot = NstRotationDate.objects.latest('num')
    new_rot = NstRotationDate.objects.create(date=d8, num=prev_rot.num + 1)
    new_rot.save()
    perm_nst = NstLocation.objects.exclude(permanent_species__isnull=True).exclude(permanent_species__exact='')
    for nst in perm_nst:
        NstSpeciesListArchive.objects.create(
            rotation_num=new_rot,
            species_txt=nst.permanent_species,
            nestid=nst
        ).save()
    print(f"Added rotation {new_rot}")


if __name__ == "__main__":
    main(None)
