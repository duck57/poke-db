#!/usr/bin/env python3
# coding=UTF-8
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

from datetime import datetime
from dateutil.parser import *
from dateutil.relativedelta import *
from collections import defaultdict
import readline
import pytz
from typing import Union, Optional, Collection

"""
Module of miscellaneous static helper functions that are re-used between modules.

NOTE on READLINE:
Importing readline here makes click act up in the all the modules that rely on this one
however, I've only noticed this with the rewrite, since I never encounter the circumstances leading to the bug in
my normal use of these programs (I always use the command line flags)
tl;dr: readline causes newlines not to happen when accepting a default value by entering nothing in click
"""


# change from a lambda to make PEP8 shut up
def nested_dict() -> defaultdict:
    """a[b][c][d][e] = 23"""
    return defaultdict(nested_dict)


def str_int(string: Union[str, int]) -> bool:
    """
    checks if a string will convert to an int
    why isn't this in the standard library?
    :param string: string to check
    :return: whether the string can convert to an integer
    """
    # this could be part of a function that returns an int if it is a string and None otherwise?
    try:
        int(string)
    except ValueError:
        return False
    return True


def parse_relative_date(date: str) -> datetime:
    """For dates of the w+3 variety"""
    today = datetime.now(tz=pytz.utc)
    date_shift = int(date[1:])
    units = date[0].lower()

    return today + {
        "y": relativedelta(years=date_shift),
        "m": relativedelta(months=date_shift),
        "w": relativedelta(weeks=date_shift),
        "t": relativedelta(days=date_shift),
        "h": relativedelta(hours=date_shift),
    }.get(units, relativedelta(seconds=0))


def parse_date(date: str = "") -> datetime:
    """Fancy wrapper for dateutil.parse that accepts m-6 formats as well"""
    date = date.strip().lower()
    if not date:
        return parse_date("t")  # return today as a default
    if date == "t":
        return parse_date(
            "t+0"
        )  # these two could be direct calls for marginal performance gain
    if date[0] in "hymwt" and len(date) > 2 and date[1] in "+-" and str_int(date[1:]):
        return parse_relative_date(date)

    d = parse(date)
    if d.tzinfo is None:
        return pytz.utc.localize(d)
    else:
        return d.astimezone(pytz.utc)


def getdate(question: str, date: Optional[str] = None) -> datetime:
    """
    gets a date (also accepts relative dates like y-1, t+3, w+2)
    will keep prompting you until you get it right
    :param date: freeform date to check
    :param question: string to prompt the user
    :return: a datetime object
    """
    date_out: Optional[datetime] = None
    while date_out is None:
        if date is None:
            date = input(question)
        try:
            date_out = parse_date(date)
        except (ValueError, TypeError):
            print("Please enter a valid date.")
            date, date_out = None, None
    return date_out


def decorate_text(text: str, decor: str) -> str:
    """
    decorates a string of text by inserting it halfway between the decoration string
    :param text: the text to decorate
    :param decor: a symmetrical string that has the text inserted at its middle
    :return: the decorated text
    """
    stl = len(decor) // 2
    return decor[:stl] + text + decor[stl:]


def true_if_y(
    st: str,
    spell_it: bool = False,
    insist_case: Optional[str] = None,
    only_yes: bool = False,
) -> bool:
    """
    :param st: string to check if it should be true or not
    :param spell_it: force the user to spell out yes instead of just Y
    :param insist_case: insist on a specific case
    :param only_yes: only accept the yes if nothing else is said
    :return: True if the first character of the string is a Y
    """
    st = st.strip()
    if not st:
        return False
    match_string: str = {
        "lower": "yes",
        "UPPER": "YES",
        # input is converted to UPPERCASE if case-matching is unimportant
        None: "YES",
        # we can guess the meaning of some bad calling code
        False: "YES",
    }.get(
        insist_case
    )  # no default so that match_string=True throws an error
    assert match_string is not None, f"Invalid value of insist_case: {insist_case}"
    if (insist_case == "lower" and st != st.lower()) or (
        insist_case == "UPPER" and st != st.upper()
    ):
        return False
    if not insist_case:
        st = st.upper()
    if not only_yes:
        st = st[:3]
    elif len(st) == 2:  # "ye"
        return False  # returns false for only_yes=True
    if spell_it:
        return True if f"{st:<3}" in match_string else False
    return True if st[0] == match_string[0] else False


def disp_qs_select(qs: Collection, none_option: Union[bool, str] = True) -> int:
    """
    Displays a QuerySet as
    :param qs: A previously-sorted QuerySet
    :param none_option: display an option 0 for 'none of the above'
    :return: the length of the options displayed (including any zeroth option)
    """
    many: int = len(qs)
    if none_option:
        many += 1
    if many < 2:
        assert (
            "Programming Error: This should be used if there are at least two options."
        )
    count: int = 1
    if str(none_option) == "True":
        none_option = "None of these"
    if none_option:
        print(f"0. {none_option}")
    for thing in qs:
        print(f"{count}. {thing}")
        count += 1
    return many


def select_from_list(prompt: str, size: int, start: int) -> int:
    """
    Prompt the user to select an item from a list
    :param prompt: Text to prompt the user
    :param size: Size of list
    :param start: Smallest number in the list
    :return: The user's selection once valid
    """
    while True:
        try:
            selection = int(input(prompt))
        except ValueError:
            print("Enter an integer")
            continue
        if selection in range(start, size + 1):
            return selection
        else:
            print("Selection outside range")
            continue


def pick_from_qs(
    prompt: str, qs: Collection, allow_none: Union[bool, str] = True
) -> int:
    """
    Pick an option from a QuerySet
    :param prompt: prompt for the user
    :param qs: query set from which the user should choose
    :param allow_none: allow the user to select a "none of these option" and return 0
    :return: the object's position number
    """
    return select_from_list(
        prompt, disp_qs_select(qs, allow_none), 0 if allow_none else 1
    )


def input_with_prefill(prompt: str, text: str) -> str:
    """
    prefills input and places your cursor at the end
    :param prompt: the prompt
    :param text: the prefill
    :return: any modifications you made to the input
    """

    def hook():
        readline.insert_text(text)
        readline.redisplay()

    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result


def local_time_on_date(
    date: datetime, hour: int, tz, minute: Optional[int] = None
) -> datetime:
    """
    :param date: date
    :param hour: hour of local time
    :param tz: timezone
    :param minute: minute of local time
    :return: a datetime object with the hour & minute appended to
    the date in the specified timezone.  Calculates whether the time
    was during DST or not.
    """
    loctm = tz.localize(datetime(date.year, date.month, date.day))
    loctm = loctm.replace(hour=hour)
    if minute is not None:
        loctm = loctm.replace(minute=minute)
    return loctm


def append_utc(naive: datetime) -> datetime:
    """Appends TZ-awareness to UTC datetimes"""
    return pytz.utc.localize(naive)
