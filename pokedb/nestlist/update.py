#!/usr/bin/env python3
# coding=UTF-8
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

import os
import sys
from datetime import datetime
import pyperclip
from utils import getdate, decorate_text, nested_dict
import click

if __name__ == '__main__':
    # Setup environ
    sys.path.append(os.getcwd())
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pokedb.settings")

    # Setup django
    import django

    django.setup()

    # now you can import your ORM models
    from nestlist.models import NstRotationDate, NstSpeciesListArchive, NstLocation, \
        NstNeighborhood, NstCombinedRegion, NstAltName
    from typeedit.models import Type


# maybe this should be in a config file in the future
private_reminder = '☝'
ghost_icon = '👻'
giraffe_icon = '🦒'
small_whale = '🐳'
large_whale = '🐋'
rat_icon = '🐀'
hoothoot = '🦉'
water_icon = '💦'


def gen_parenthetical(notes):
    """
    generates a parenthetical containing notes and a private property notice when needed
    assumes at least one of these is true or populated
    :param notes: notes about the nest (list of strings)
    :return: a parenthetical statement containing notes and any private property reminders
    """

    return decorate_text('; '.join(notes), '()')


def FB_format_nests(nnl):
    """
    Facebook-specific formatting
    :param nnl: nested_dict in the form of nnl[location][nest], where location is text and nest is a NSLA object
    :return: a formatted string of all the nests arranged alphabetically by park divided by neighborhood/region
    """

    list_txt = ""
    for location in sorted(nnl.keys()):
        # use "ZZZ" instead of just "Z" to accommodate Zanesville
        # and any city that two consecutive Z in its name
        list_txt += decorate_text(location.split("ZZZ")[-1], "{~()~}") + '\n'
        for nest in sorted(nnl[location]):
            # nest = nnl[location][nest_txt]
            if nest.species_name_fk is not None \
                    and nest.species_name_fk.is_type(Type.objects.get(id=8)):  # type 8 is Ghost
                list_txt += ghost_icon
            if nest.nestid.private is True:
                list_txt += private_reminder  # private property reminder
            list_txt += nest.nestid.get_name()  # nest name
            alts = NstAltName.objects.filter(main_entry=nest.nestid).exclude(hide_me=True)
            if len(alts) > 0:
                for alt in alts:
                    list_txt += "/" + alt.name
            if nest.nestid.notes is not None or nest.special_notes is not None:
                notef = []
                if nest.nestid.notes is not None:
                    notef.append(nest.nestid.notes)
                if nest.special_notes is not None:
                    notef.append(nest.special_notes)
                list_txt += " " + gen_parenthetical(notef)
            list_txt += ": " + (nest.species_name_fk.name if nest.species_name_fk is not None else nest.species_txt)
            if nest.confirmation is not True:
                list_txt += "*"
            list_txt += '\n'  # prepare for next item
        list_txt += '\n'
    return list_txt


def FB_empty(empties):
    """
    Handle parks with no reports for Facebook
    :param empties: nested_dict of empty nests in the form of empties[Neighborhood][nest] = NstLocation object
    :return: formatted string of parks arranged by neighborhood
    """

    mt_txt = decorate_text("No Reports", "[--  --]") + '\n'
    for location in sorted(empties.keys()):
        mt_txt += "• " + location + ": "
        first = True
        for park in empties[location]:
            if first is False:
                mt_txt += ", "
            if park.private:
                mt_txt += private_reminder
            mt_txt += park.get_name()
            first = False
        mt_txt += '\n'
    return mt_txt


def annotate_species_txt(species_txt):
    """
    :param species_txt: string to check against
    :return: an emoji or an empty string to match the species
    """

    if species_txt == 'Water Biome':
        return water_icon
    if species_txt == 'Wailmer':
        return small_whale
    if species_txt == 'Wailord':
        return large_whale
    if species_txt == 'Girafarig':
        return giraffe_icon
    if species_txt == 'Hoothoot':
        return hoothoot
    if species_txt == 'Rattata':
        return rat_icon
    return ''


def annotate_species(nest):
    """
    :param nest: NSLA object
    :return: an emoji or empty string
    """

    if nest.species_name_fk is None:
        return annotate_species_txt(nest.species_txt)
    if nest.species_name_fk.is_type(Type.objects.get(id=8)):  # Ghost-type ID = 8
        return ghost_icon
    if nest.species_name_fk.name == 'Wailmer':
        return small_whale
    if nest.species_name_fk.name == 'Wailord':
        return large_whale
    if nest.species_name_fk.name == 'Girafarig':
        return giraffe_icon
    if nest.species_name_fk.name == 'Hoothoot':
        return hoothoot
    if nest.species_name_fk.name == 'Rattata':
        return rat_icon
    return ''


def FB_summary(summary):
    """
    :param summary: nested_dict in form summary[species][park] = park, where species is a string and park is NSLA
    :return: formatted string of nests organized by species
    """

    out = decorate_text("Summary", "[--  --]")
    for species in sorted(summary.keys()):
        out += "\n" + annotate_species_txt(species) + species + ": "
        first = True
        for nest in summary[species]:
            if first is False:
                out += ", "
            if nest.nestid.private:
                out += private_reminder
            out += nest.nestid.get_name()
            if nest.confirmation is not True:
                out += "*"
            first = False
    out += "\n\n"
    return out


def FB_preamble(updated8, rotationday, rotnum):
    """
    dates should be previously-formatted as strings
    :param updated8: string for the date of the update generation
    :param rotationday: string for the rotation date
    :param rotnum: rotation number (int)
    :return: Preamble for FB post
    """

    out = "#Nests #Tracking #Migration\n"
    out += "* = Unconfirmed, "
    out += private_reminder + "️ = Private property, please be respectful\n"
    out += rotationday + " nest shift (#" + str(rotnum) + ")\n"
    out += "Last updated: " + updated8 + "\n\n"
    return out


def disc_preamble(updated8, rotationday, rotnum):
    """
    dates should be previously-formatted as strings
    :param updated8: string for the date of the update generation
    :param rotationday: string for the rotation date
    :param rotnum: rotation number (int)
    :return: Preamble for Discord post
    """

    out = decorate_text(rotationday, "``") + " nest shift (#" + str(rotnum) + ")\n"
    out += "Last updated: " + updated8 + "\n\n"
    out += "**Bold** species are confirmed; _italic_ are single-reported\n\n"
    return out


def disc_important_species(slist):
    """
    discord post of top/important species & parks
    maybe this should be from a config file?
    :param slist: species-arranged nested_dict, like elsewhere
    :return: a species summary for the popular species
    """

    important_species = ["Magikarp", "Walimer", "Water Biome"]
    out = decorate_text("Popular Species", "__****__")
    count = 0
    for species in sorted(slist.keys()):
        if species not in important_species and slist[species]["-Spooked"] is not True:
            continue
        count += 1
        out += '\n• ' + species + ": "
        first = True
        for park in slist[species]:
            if park == "-Spooked":
                continue
            if first is False:
                out += ', '
            out += decorate_text(park, '****' if slist[species][park]["Status"] == 2 else '__')
            first = False
    if count == 0:
        return ''
    return out


def disc_posts(nnl2, rundate, shiftdate, slist=None, rotnum=0):
    """
    generate and copy a Discord post to the clipboard

    assumes all lines are roughly the same length and you don't troll with a 2000+ chars line for a single region

    :param nnl: nested_dict in the format of nnl[area][nest] = NSLA object
    :param rundate: string of the date the list was generated
    :param shiftdate: string of the date of the nest shift
    :param mt: nested_dict of empty nests—mt[nest] = NstLocation object
    :param slist: nested_dict of species-sorted nests—slist[species][nest] = NSLA object
    :param rotnum: rotation number (int)
    :return:
    """

    list = []
    olen = 0
    max = 2000  # Discord post length limit
    pre = disc_preamble(rundate, shiftdate, rotnum)
    olen += len(pre)
    list.append('')  # this is required for things to split up right later
    list.append(pre)

    for loc in sorted(nnl2.keys()):
        loclst = decorate_text(loc, '__****__') + '\n'
        for nestname in sorted(nnl2[loc].keys()):
            loclst += nestname
            nest = nnl2[loc][nestname]
            if nest["Alt"] != '':
                loclst += '/' + str(nest["Alt"])
            loclst += ": " + decorate_text(nest["Species"], '****' if nest["Status"] == 2 else '__') + '\n'
        if len(loclst) > 2000:
            raise Exception("Nest list for sub-region " + loc + """ exceeds 2000 characters,
            which causes Discord problems.  Consider breaking into smaller areas.""")
        olen += len(loclst)
        list.append(loclst)

    start = 0
    end = 0
    num = olen // max + 1
    trg = olen // num
    outparts = []
    pts = len(list) // num
    ix = 0
    count = 0
    tmpstr = ""
    for nbh in list:
        if len(nbh) + count < max and count <= trg:
            tmpstr += nbh
            count += len(nbh)
        else:
            outparts.append(tmpstr)
            tmpstr = nbh
            count = 0
            ix += 1
    outparts.append(tmpstr)

    outparts.append(disc_important_species(slist))

    pos = 0
    num = len(outparts)
    for part in outparts:
        pyperclip.copy(part)
        pos += 1
        if pos < num:
            input(f"Copied part {pos} of {num} to the clipboard. Press enter or return to continue.")
        else:
            print(f"Copied part {pos} of {num} to the clipboard.")


def FB_post(nnl, rundate, shiftdate, mt=None, slist=None, rotnum=0):
    """
    generate and copy a Facebook post to the clipboard
    :param nnl: nested_dict in the format of nnl[area][nest] = NSLA object
    :param rundate: string of the date the list was generated
    :param shiftdate: string of the date of the nest shift
    :param mt: nested_dict of empty nests—mt[nest] = NstLocation object
    :param slist: nested_dict of species-sorted nests—slist[species][nest] = NSLA object
    :param rotnum: rotation number (int)
    :return:
    """

    post = FB_preamble(rundate, shiftdate, rotnum)
    if slist is not None:
        post += FB_summary(slist)
        post += decorate_text(" • ", "---==<>==---") + "\n\n"
    post += FB_format_nests(nnl)
    if mt is not None:
        # post += decorate_text(" • ", "---==<>==---") + "\n\n"
        post += FB_empty(mt)
    pyperclip.copy(post)
    print("Nest list copied to clipboard")


def get_rot8d8(today):
    """
    select the most recent date on or before the supplied date from the database
    :param today: date to check
    :return: rotation corresponding to the most recent one on or before the supplied date
    """

    res = NstRotationDate.objects.filter(date__lte=today).order_by('-num')
    if len(res) > 0:
        return res[0]
    print(f"Date {today} is older than anything in the database.  Using oldest data instead.")
    return NstRotationDate.objects.all().order_by('date')[0]


def nestname(nestrow):
    """
    Returns the preferred name of a nest, currently set to the short name
    :param nestrow: NstLocation object
    :return: The name
    """

    return nestrow.short_name if nestrow.short_name is not None else nestrow.official_name


def get_nests(rotnum):
    """
    :param rotnum: rotation ID
    :return: the nested nest list, a stack of empties, and the list sorted by species
    """

    nestout = {}
    nestmt = nested_dict()
    ssumry = nested_dict()

    nests = NstSpeciesListArchive.objects.filter(rotation_num=rotnum)
    empties = NstLocation.objects.exclude(nstrotationdate=rotnum).order_by('official_name')
    neighborhoods = NstNeighborhood.objects.filter(nstlocation__nstrotationdate=rotnum)\
        .order_by('name')
    regions = NstCombinedRegion.objects.filter(nstneighborhood__in=neighborhoods).order_by('name')
    neighborhoods = neighborhoods.exclude(region__gt=0)  # clever way to check for non-null regions in a neighborhood

    for neighborhood in neighborhoods:
        nestout[neighborhood.name] = set()
    for region in regions:
        nestout[region.name] = set()

    for nest in nests:
        nname = nest.nestid.get_name()
        region = nest.nestid.neighborhood.region
        if region is None:
            nestout[nest.nestid.neighborhood.name].add(nest)
        else:
            nestout[region.name].add(nest)
        if nest.species_name_fk is None:
            ssumry[nest.species_txt][nest] = nest
        else:
            ssumry[nest.species_name_fk.name][nest] = nest

    for empty in empties:
        nestmt[empty.neighborhood.name][empty] = empty

    return nestout, nestmt, ssumry


@click.command()
@click.option(
    '-d',
    '--date',
    default=str(datetime.today().date()),
    prompt="Generate list of nests as of this date",
    help="Generate list of nests as of this date"
)
@click.option(
    '-o',
    '--format',
    type=click.Choice(['FB', 'Facebook', 'f', 'd', 'Discord', 'disc']),
    prompt="Output format",
    help="Specify the output formatting for the nest list")
def main(date=None, format=None):
    """
    Main method
    :param date: date to generate the list for
    :param format: output format
    :return: nothing
    """

    date = getdate("For which date do you wish to generate the nests list?: ", date)
    run_date = date.strftime('%d %b %Y')
    print(f"Gathering nests as of {run_date}")

    rotation = get_rot8d8(date)
    shiftdate = str(rotation.date)
    rotnum = int(rotation.num)
    nests, empties, species = get_nests(rotation)
    print(f"Using the nest list from the {shiftdate} nest rotation")
    if format[0].lower() == 'f':
        # format_name = "Facebook"
        FB_post(nests, run_date, shiftdate, slist=species, mt=empties, rotnum=rotnum)
    if format[0].lower() == 'd':
        # format_name = "Discord"
        disc_posts(nests, run_date, shiftdate, slist=species, rotnum=rotnum)


if __name__ == "__main__":
    main()
