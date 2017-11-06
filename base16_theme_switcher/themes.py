# -*- coding: utf-8 -*-
import re
from os.path import basename, splitext
from string import ascii_uppercase, digits


class InvalidThemeError(ValueError):
    """A color theme is invalid."""

    def __init__(self, theme, color_def_error, color_name):
        """Create a new instance.

        :param theme: a string representing an invalid theme.
        :param color_def_error: an adjective describing an error with
            a color definition, like "invalid", "unexpected" or
            "missing".
        :param color_name: a name of a color whose definition is
            invalid.
        """
        super().__init__(
            '{} color definition in {}: {}'.format(
                color_def_error.capitalize(), theme, color_name)
        )


class Base16Theme:
    """Represents a base16 color theme loaded from an .Xresources file.

    Base16 color theme format specification:
        https://github.com/chriskempson/base16/blob/master/styling.md

    The format is simple: it requires only 16 colors to be defined with
    specific names, from base01 to base0F. It's hard to make a mistake
    in a new theme, and the base16-xresources project provides plety
    of valid themes already. For these reasons, the class doesn't
    perform strict validation for each color in each theme.

    The validations the class does perform are only a couple of sanity
    checks, performed lazily for a color of a theme requested by calling
    __getitem__ method of this class.

    Since the contents of the file are not needed until a theme is
    applied, the file is read lazily and only upon requesting
    definitions it contains (see definitions property and __getitem__
    method).
    """

    _DEF_PATTERN = re.compile(r'#define (\S+) (\S+)')
    """A pattern matching an .Xresources variable definition."""

    _VAL_PATTERN = re.compile(r'\#[0-9a-fA-F]{6}')
    """A pattern matching a valid hexadecimal color string."""

    _EXPECTED_COLORS = ['base0' + c for c in (digits + ascii_uppercase)[:16]]
    """Names of all colors expected to be set in a theme file."""

    def __init__(self, path):
        """Create a new instance.

        :param path: a path to an .Xresources file containing color
            definitions.
        """
        self.path = path
        self.name = splitext(basename(str(path)))[0]
        self._definitions = {}

    @property
    def definitions(self):
        """Get definitions provided by the file.

        :returns: a map of names defined in the file to their respective
            values.
        """
        if not self._definitions:
            self._definitions = dict(
                self._DEF_PATTERN.findall(self.path.read_text())
            )
        return self._definitions

    def __getitem__(self, name):
        """Get a color defined in the theme.

        :param name: a name of a color value to be returned.
        :returns: the requested color.
        :raises KeyError: if the name is not expected for a base16 color
            theme (see specification).
        :raises InvalidThemeError: if the requested color is part of
            the specification, but is not defined in the theme, or if
            the value of requested color is not a valid hexadecimal
            color code.
        """
        if name not in self._EXPECTED_COLORS:
            raise KeyError(
                'An unsupported color was requested: {}'.format(name)
            )

        try:
            value = self.definitions[name]
        except KeyError:
            self._raise_invalid_theme_error('missing', name)

        if not self._VAL_PATTERN.match(value):
            self._raise_invalid_theme_error('invalid', name)

        return value

    def _raise_invalid_theme_error(self, descr, color_name):
        raise InvalidThemeError(self.path, descr, color_name)

    def __str__(self):
        """Get a string representation of the theme.

        :returns: the path of the theme file as a string.
        """
        return str(self.path)

    @classmethod
    def find_all_in(cls, path):
        """Find all themes in a directory.

        :param path: an object representing a path to a directory to be
            searched for themes.
        :returns: a generator yielding themes.
        """
        with path:
            for f in path.rglob('*.Xresources'):
                yield cls(f)
