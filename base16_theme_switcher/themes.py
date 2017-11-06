# -*- coding: utf-8 -*-


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
