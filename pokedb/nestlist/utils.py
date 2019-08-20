#!/usr/bin/env python3
# coding=UTF-8
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

from datetime import datetime
from dateutil.parser import *
from dateutil.relativedelta import *
from collections import defaultdict
import readline

# note: importing readline here makes click act up in the all the modules that rely on this one
# however, I've only noticed this with the rewrite, since I never encounter the circumstances leading to the bug in
# my normal use of these programs (I always use the command line flags)
# tl;dr: readline causes newlines not to happen when accepting a default value by entering nothing in click


nested_dict = lambda: defaultdict(nested_dict)


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


def getdate(question, date=None):
    """
    gets a date (also accepts relative dates like y-1, t+3, w+2)
    will keep prompting you until you get it right
    :param date: freeform date to check
    :return: a datetime object
    """

    today = datetime.today()
    # question = f"What is the date of the nest rotation (blank for today, {today.date()})? "

    while True:
        if date is None:
            date = input(question)
        if date.strip() == "" or (len(date) == 1 and date[0].lower() == "t"):
            return today.date()
        if (
            date[0].lower() in "ymwt"
            and len(date) > 2
            and date[1] in "+-"
            and str_int(date[1:])
        ):
            date_shift = int(date[1:])
            units = date[0].lower()
            create_date = today + {
                "y": relativedelta(years=date_shift),
                "m": relativedelta(months=date_shift),
                "w": relativedelta(weeks=date_shift),
                "t": relativedelta(days=date_shift),
            }.get(units, 0)
            return create_date.date()
        try:
            return parse(date).date()
        except (ValueError, TypeError):
            print("Please enter a valid date.")
            date = input(question)


def decorate_text(text, decor):
    """
    decorates a string of text by inserting it halfway between the decoration string
    :param text: the text to decorate
    :param decor: a symmetrical string that has the text inserted at its middle
    :return: the decorated text
    """

    stl = len(decor) // 2
    return decor[:stl] + text + decor[stl:]


def true_if_y(st):
    """
    :param st: string to check
    :return: True if the first character of the string is a Y (case-insensitive)
    """

    if st.strip() == "":
        return False
    if st[0].upper() == "Y":
        return True
    return False


def disp_qs_select(qs, none_option=True):
    """
    :param qs: A previously-sorted QuerySet
    :param none_option: display an option 0 for 'none of the above'
    :return: the length of the query set
    """

    many = len(qs)
    if many < 2:
        assert (
            "Programming Error: This should be used if there are at least two options."
        )

    count = 1

    if none_option is True:
        none_option = "None of these"

    if none_option is not False:
        print(f"0. {none_option}")
    for thing in qs:
        print(f"{count}. {thing}")
        count += 1

    return many


def select_from_list(prompt, size, start):
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


def pick_from_qs(prompt, qs, allow_none=True):
    """
    Pick an option from a QuerySet
    :param prompt: prompt for the user
    :param qs: query set from which the user should choose
    :param allow_none: allow the user to select a "none of these option" and return 0
    :return:
    """
    maxi = disp_qs_select(qs, allow_none)
    return select_from_list(prompt, maxi, 0 if allow_none else 1)


def input_with_prefill(prompt, text):
    """

    :param prompt:
    :param text:
    :return:
    """

    def hook():
        readline.insert_text(text)
        readline.redisplay()

    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result
