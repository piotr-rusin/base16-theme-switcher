# -*- coding: utf-8 -*-
"""Parsing command-line arguments and executing the application."""

import argparse

from base16_theme_switcher import app


parser = argparse.ArgumentParser(
    description=(
        'Set an .Xresources based color theme for supported applications.\n'
    )
)
parser.add_argument(
    '-c', '--config', type=str,
    default='~/.config/base16-theme-switcher/config.yml',
    help='A configuration file to be used for the theme switcher.'
)
parser.add_argument(
    '-l', '--log', type=str,
    default='~/.logs/base16-theme-switcher/latest.log',
    help='An output file for latest logs.'
)
parser.add_argument(
    '-v', '--verbose', type=bool, default=False,
    help=(
        'Print not only errors, but also debug messages in standard output.'
    )
)

group = parser.add_mutually_exclusive_group()

group.add_argument(
    'theme_name', type=str, nargs='?', default=None,
    help='A name of a theme to be set.'
)

group.add_argument(
    '-r', '--reload', type=bool, default=False,
    help='Reload an already set theme.'
)

arguments = parser.parse_args()
app.main(arguments)
