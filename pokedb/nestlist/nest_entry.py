#!/usr/bin/env python3
# coding=UTF-8
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

import readline
from collections import defaultdict

import click

import importoldlists as dbutils
import rotate as dateparse
import update as output

nested_dict = lambda: defaultdict(nested_dict)


def selectlist(prompt, size, start):
    while True:
        try:
            selection = int(input(prompt))
        except (ValueError):
            print("Enter an integer")
            continue
        if selection in range(start, size + 1):
            return selection
        else:
            print("Selection outside range")
            continue


def input_with_prefill(prompt, text):
    def hook():
        readline.insert_text(text)
        readline.redisplay()

    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result


def search_nest_query(dbc, search):
    if dateparse.str_int(search):
        result = dbc.execute("SELECT * FROM nest_locations WHERE nest_id = ?", [search]).fetchone()
        if result is not None:
            return [result]
    results1, _ = dbutils.query_nest(search, dbc)
    if results1 is None:
        print("No nests found")
        return False
    return results1


# returns the park ID of the selected park
def disp_park_list(dbc, results1):
    count = 0
    results2 = nested_dict()
    choices = {}
    for nest in results1:
        nid = nest[0]
        if nid in choices.values():
            continue
        else:
            count += 1  # it goes here or else later logic is wrong
        choices[count] = nid
        results2[nid]["Name"] = nest[1]
        results2[nid]["Short"] = nest[2]
        results2[nid]["LocID"] = nest[3]
        results2[nid]["Count"] = count
    choices[0] = None
    results2[None]["Name"] = "None of these"
    for choice in sorted(choices.keys()):
        if choice == 0:
            print("0. None of these")
            continue
        neighborhood = "Missing"
        if results2[choices[choice]]["LocID"] is not None:
            neighborhood = \
            dbc.execute("SELECT name FROM neighborhoods WHERE id = ?", [results2[choices[choice]]["LocID"]]).fetchone()[
                0]
        print(str(choice) + ". " + results2[choices[choice]]["Name"], " [" + neighborhood + "]")
    selected = -1
    if count == 1:
        selected = 1
    else:
        selected = selectlist("Enter the number of the park you would like to display: ", count, 0)
    return choices[selected]


def match_species(dbc, sptxt):
    reslst = nested_dict()
    num = 0
    for result in dbc.execute("SELECT * FROM nesting_species WHERE Name like ?", ['%' + sptxt + '%']):
        num += 1
        reslst[num] = result
    if len(reslst) == 0:
        return None, sptxt
    if len(reslst) == 1:
        return reslst[1][0], reslst[1][1]
    reslst[0] = (None, sptxt)
    for item in reslst:
        print(str(item) + '. ' + reslst[item][1] + ' [' + str(reslst[item][0]) + ']')
    option = selectlist("Index of species (not species number): ", num, 0)
    return reslst[option][0], reslst[option][1]


def update_park(dbc, rotnum):
    print("q to quit without saving, empty to quit & commit changes")
    search = input("Which park do you want to search? ").strip().lower()
    if search == '':
        return 1
    if search == 'q':
        return -5
    results1 = search_nest_query(dbc, search)
    if results1 is False:
        return False

    selected = disp_park_list(dbc, results1)
    if selected is None:
        return False

    sq1 = "SELECT * FROM nest_locations WHERE nest_id=?"
    sq2 = "SELECT * FROM alt_names WHERE main_entry=?"
    sq3 = "SELECT * FROM neighborhoods WHERE id=?"
    sq4 = "SELECT * FROM regions WHERE id=?"
    nest_info = """
        SELECT
            nest_locations.*,
            neighborhoods.name AS 'Subdivision',
            regions.*
        FROM nest_locations
            LEFT OUTER JOIN neighborhoods ON nest_locations.location = neighborhoods.id
            LEFT OUTER JOIN regions ON neighborhoods.region = regions.id
        WHERE nest_id = ?"""

    inforow = dbc.execute(nest_info, [selected]).fetchall()[0]
    alts = dbc.execute(sq2, [selected])
    sinforow = []
    for i in inforow:
        sinforow.append(str(i))

    """print("Nest id: " + sinforow[0])
    print("Name: " + sinforow[1])
    print("Short: " + sinforow[2])
    print("Neighborhood id: " + sinforow[3])
    print("Address: " + sinforow[4])
    print("Notes: " + sinforow[5])
    print("Private? " + sinforow[6])
    print("Fixed nest? " + sinforow[7])
    print("Latitude: " + sinforow[8])
    print("Longitude: " + sinforow[9])
    print("Nest size: " + sinforow[10])
    print("Neighborhood: " + sinforow[11])
    print("Region ID: " + sinforow[12])
    print("Region: " + sinforow[13])
    print(output.decorate_text("Alternate Names", "[--  --]"))
    for alt in alts:
        print(str(alt))"""

    print("\nSelected Nest: " + sinforow[0] + " " + sinforow[1])
    rwnst = dbc.execute("SELECT species_txt, confirmation FROM species_list WHERE rotation_num = ? AND nestid = ?",
                        (rotnum, inforow[0])).fetchall()
    current, confirm = None, None
    if len(rwnst) > 0:
        current = rwnst[0][0]
        confirm = rwnst[0][1]
    upd8nest = "UPDATE species_list SET species_no = ?, species_txt = ?, confirmation = ? WHERE rotation_num = ? AND nestid = ?"
    svnstsql = "INSERT INTO species_list(species_no, species_txt, confirmation, rotation_num, nestid) VALUES (?,?,?,?,?)"
    delnest = "DELETE FROM species_list WHERE rotation_num = ? AND nestid = ?"
    if current is None:
        current = ''
        upd8nest = svnstsql  # adds a new nest if it's currently empty
    elif confirm is not None:
        current += "|" + str(confirm)
    species = input_with_prefill("Species|confirm? ", current).strip()
    print("")

    conf = 1 if len(species.split('|')) > 1 else None
    species = species.split('|')[0].strip()
    spnum = None
    if species == '':
        species = None
        dbc.execute(delnest, (rotnum, inforow[0]))
        return False
    if dateparse.str_int(species):
        spnum = int(species)
        species = dbc.execute("SELECT * FROM nesting_species WHERE `#` = ?", [spnum]).fetchone()
        if species is not None:
            species = species[1]
        else:
            print(f"#{spnum:03} is not a nesting species.  No changes applied.")
            return False  # something to prevent the insertion of junk nests?
    else:
        spnum, species = match_species(dbc, species)
    if spnum is None:
        print(f"Using verbatium species as a string and not a species number")
    savenest = (spnum, species, conf, rotnum, inforow[0])
    dbc.execute(upd8nest, savenest)

    return False


@click.command()
@click.option(
    '-d',
    '--date',
    default="today",
    prompt="Date to edit",
    help="Date you choose to edit, can be absolute (YYYY-MM-DD) or relative (w+2)"
)
def main(date):
    dbc = dbutils.create_connection("nests.db")
    rotnum, d8 = output.get_rot8d8(dateparse.getdate(date), dbc)
    print("Editing rotation " + str(rotnum) + " from " + d8)
    stop = False
    while stop is False:
        stop = update_park(dbc, rotnum)
    if stop == 1:
        dbc.commit()
        print("Nests saved!")
    else:
        dbc.rollback()
        print("Nests reverted")
    dbc.close()


if __name__ == "__main__":
    main()
