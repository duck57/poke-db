#!/usr/bin/env python3
# coding=UTF-8
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :

import click

# import readline


"""
This is a test file to show how click and readline don't get along

Uncomment the instruction to jump to home in main to cause a click error on
prompts that aren't at the command line

Uncomment the readline import and then hit enter at the click prompt to reveal
a lack of newline bug """


# @click.command()
@click.option("test", prompt="Is this a test")
def home(test):
    click.echo(test)


@click.command()
@click.option("--count", default=1, help="Number of greetings.")
@click.option("--name", prompt="Your name", help="The person to greet.")
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    for x in range(count):
        click.echo("Hello %s!" % name)
    # home(None)


if __name__ == "__main__":
    hello()
