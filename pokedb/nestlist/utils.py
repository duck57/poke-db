#!/usr/bin/env python3
# coding=UTF-8
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

from datetime import datetime
from math import cos, sin, atan2, degrees, radians, sqrt, log, tan, pi

from dateutil.parser import *
from dateutil.relativedelta import *
from collections import defaultdict
import readline
import pytz
from typing import Union, Optional, Collection, List, Tuple, Callable

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
    date = str(date).strip().lower()
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


def class_lookup(cls) -> set:
    """Returns the class hierarchy for a class"""
    return set(type.mro(cls))


def pretty_class_lookup(cls) -> None:
    """Pretty output for class_lookup"""
    for c in class_lookup(cls):
        print(c)


def compare_classes(c1, c2) -> set:
    """Returns the common parent classes of two classes"""
    return class_lookup(c1) & class_lookup(c2)


def constrain_degrees(m: float) -> float:
    return (m + 180) % 360 - 180


def cardinal_direction_from_bearing(
    bearing: float,
    *,
    emoji: bool = False,
    chr_lst: Optional[List[str]] = None,
    in_radians: bool = False,
) -> str:
    """
    :param chr_lst: provide your own char list with direction indices that correspond to the arrows on a numeric keypad
    :param emoji: use predefined emoji arrows
    :param bearing: orienteering bearing (0° is North, clockwise)
    :param in_radians: it's in radians
    :return: compass direction
    """
    if in_radians:
        bearing = degrees(bearing)
    sections: int = 8
    interval: float = 360 / sections
    offset: float = interval / 2
    bearing = (bearing - offset) % 360  # normalize the if statements
    if not chr_lst:
        chr_lst = (
            ["💣", "↙️", "⬇️", "↘️", "⬅️️", "🚏", "➡️", "↖️", "⬆️", "↗️"]
            if emoji
            else ["", "SW", "S", "SE", "W", "here", "E", "NW", "N", "NE"]
        )
    # there's got to be some more clever way to do this
    if 0 * interval <= bearing <= 1 * interval:
        return chr_lst[9]  # northeast
    if 1 * interval <= bearing <= 2 * interval:
        return chr_lst[6]  # east
    if 2 * interval <= bearing <= 3 * interval:
        return chr_lst[3]  # southeast
    if 3 * interval <= bearing <= 4 * interval:
        return chr_lst[2]  # south
    if 4 * interval <= bearing <= 5 * interval:
        return chr_lst[1]  # southwest
    if 5 * interval <= bearing <= 6 * interval:
        return chr_lst[4]  # west
    if 6 * interval <= bearing <= 7 * interval:
        return chr_lst[7]  # northwest
    if bearing >= 7 * interval:
        return chr_lst[8]  # north
    return chr_lst[0]  # error


def cv_geo_tuple(t: Tuple[float, float], f: Callable) -> Tuple[float, float]:
    return f(t[0]), f(t[1])


EARTH_RADIUS: float = 6371


def initial_bearing(
    here: Tuple[float, float], there: Tuple[float, float], *, in_radians: bool = False
) -> float:
    here, there, d_lat, d_lon, d_psi = rhumb_setup(here, there, in_radians)

    numerator = sin(d_lon) * cos(there[0])
    denominator = cos(here[0]) * sin(there[0]) - sin(here[0]) * cos(there[0]) * cos(
        d_lon
    )
    out = atan2(numerator, denominator)
    return out if in_radians else degrees(out) % 360


def angle_between_points_on_sphere(
    here: Tuple[float, float],
    there: Tuple[float, float],
    *,
    in_radians: bool = True,
    out_radians: bool = True,
) -> float:
    here, there, d_lat, d_lon, d_psi = rhumb_setup(here, there, in_radians)

    a = pow(sin(d_lat / 2), 2) + cos(here[0]) * cos(there[0]) * pow(sin(d_lon / 2), 2)
    out = 2 * atan2(sqrt(a), sqrt(1 - a))
    return out if out_radians else degrees(out)


def rhumb_setup(
    here: Tuple[float, float], there: Tuple[float, float], in_radians: bool = True
) -> Tuple[Tuple[float, float], Tuple[float, float], float, float, float]:
    if not in_radians:
        here = cv_geo_tuple(here, radians)
        there = cv_geo_tuple(there, radians)
    d_lat: float = there[0] - here[0]
    d_lon: float = there[1] - here[1]

    d_psi: float = log(tan(pi / 4 + there[0] / 2) / tan(pi / 4 + here[0] / 2))
    if abs(d_lon) > pi:  # take the shortest way
        d_lon = -(2 * pi - d_lon) if d_lon > 0 else 2 * pi + d_lon

    return here, there, d_lat, d_lon, d_psi


def loxo_len(
    here: Tuple[float, float],
    there: Tuple[float, float],
    *,
    in_radians: bool = True,
    radius: float = EARTH_RADIUS,
) -> float:
    here, there, d_lat, d_lon, d_psi = rhumb_setup(here, there, in_radians)

    q: float = d_lat / d_psi if abs(d_psi) > 10e-12 else cos(here[0])
    return sqrt(d_lat * d_lat + q * q * d_lon * d_lon) * radius


def constant_bearing_between_points_on_sphere(
    here: Tuple[float, float],
    there: Tuple[float, float],
    *,
    in_radians: bool = True,
    out_radians: bool = True,
) -> float:
    here, there, d_lat, d_lon, d_psi = rhumb_setup(here, there, in_radians)

    bearing = atan2(d_lon, d_psi)  # radians in range[-π,π]
    return bearing if out_radians else (degrees(bearing) + 360) % 360


def number_format(x: float, d: int) -> str:
    """
    Formats a number such that adding a digit to the left side of the decimal
    subtracts a digit from the right side
    :param x: number to be formatter
    :param d: number of digits with only one number to the left of the decimal point
    :return: the formatted number
    """
    assert d >= 0, f"{d} is a negative number and won't work"
    x_size: int = 0 if not x else int(log(abs(x), 10))  # prevent error on x=0
    n: int = 0 if x_size > d else d - x_size  # number of decimal points
    return f"{x:,.{n}f}"
