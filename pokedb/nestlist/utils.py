#!/usr/bin/env python3
# coding=UTF-8
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

from datetime import datetime
from dateutil.parser import *
from dateutil.relativedelta import *


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


def getdate(date=None):
    """
    gets a date (also accepts relative dates like y-1, t+3, w+2)
    will keep prompting you until you get it right
    :param date: freeform date to check
    :return: a datetime object
    """

    today = datetime.today()
    question = f"What is the date of the nest rotation (blank for today, {today.date()})? "

    while True:
        if date is None:
            date = input(question)
        if date.strip() == "" or (len(date) == 1 and date[0].lower() == "t"):
            return today.date()
        if date[0].lower() in "ymwt" and len(date) > 2 and date[1] in "+-" and str_int(date[1:]):
            date_shift = int(date[1:])
            units = date[0].lower()
            create_date = today + {
                'y': relativedelta(years=date_shift),
                'm': relativedelta(months=date_shift),
                'w': relativedelta(weeks=date_shift),
                't': relativedelta(days=date_shift)
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
    if st[0].upper() == 'Y':
        return True
    return False
