# -*- coding: utf-8 -*-
from unittest import TestCase
from unittest.mock import Mock, MagicMock

from parameterized import parameterized

from base16_theme_switcher.themes import (
    Base16Theme,
    Base16ThemeNameMap,
    DuplicateThemeNameError,
    InvalidThemeError,
)


class Base16ThemeTest(TestCase):
    """Tests for Base16Theme class."""

    def setUp(self):
        self.theme_name = 'example-theme'
        self.path_str = (
            '/home/example/.base16-themes/{}.Xresources'
            ''.format(self.theme_name)
        )
        self.path = MagicMock()
        self.path.__str__.return_value = self.path_str
        self.tested = Base16Theme(self.path)

    def test_name(self):
        """Test if the instance has the expected name attribute."""
        self.assertEqual(self.theme_name, self.tested.name)

    def test_str_returns_path_string(self):
        """Test if the instance has the expected string representation."""
        self.assertEqual(self.path_str, str(self.tested))

    def test_path(self):
        """Test if the instance has the expected path attribute."""
        self.assertEqual(self.path, self.tested.path)

    def test_getitem_returns_color(self):
        """Test if an expected color defined in the theme is returned."""
        name = 'base01'
        expected_value = '#010101'
        self.path.read_text.return_value = (
            '#define {} {}'.format(name, expected_value)
        )
        actual_value = self.tested[name]
        self.assertEqual(expected_value, actual_value)

    @parameterized.expand([
        ('unexpected_but_defined_color_request', '#define invalid01 #010101'),
        ('unexpected_color_request', '#define base01 #ffffff')
    ])
    def test_getitem_raises_KeyError_for(self, _, content):
        """Test if KeyError is raised for an unsupported color name.

        The same error should be raised whether a color with requested
        name is defined in a theme or not.

        :param content: a content of the theme file represented by
            the mocked path.
        """
        self.path.read_text.return_value = content
        msg = 'An unsupported color was requested: invalid01'
        with self.assertRaisesRegex(KeyError, msg):
            _ = self.tested['invalid01']

    @parameterized.expand([
        ('missing_color', ''),
        ('invalid_color', '#define base01 #fffggg')
    ])
    def test_getitem_raises_InvalidThemeError_for(self, error, content):
        """Test if the error is raised as expected.

        The error is expected to be raised when requesting either a color
        value whose value in theme file turns out to be invalid or a
        color that is expected to be defined in a base16 theme file,
        but is missing.

        :param error: a description of error in a color definition.
        :param content: a content of a theme file to trigger the error.
        """
        self.path.read_text.return_value = content
        msg = '{} color definition in {}: base01'.format(
            error.replace('_color', '').capitalize(),
            self.path_str
        )
        with self.assertRaisesRegex(InvalidThemeError, msg):
            _ = self.tested['base01']

    def test_find_all_in(self):
        """Test if the class method returns expected theme objects.

        The expected theme objects are instances of Base16Theme
        representing all .Xresources files found under a directory with
        given path.
        """
        expected_paths = [Mock() for _ in range(4)]
        dir_path = MagicMock()
        dir_path.rglob.side_effect = (
            lambda c: expected_paths if c == '*.Xresources' else []
        )

        actual_paths = [t.path for t in Base16Theme.find_all_in(dir_path)]
        self.assertCountEqual(expected_paths, actual_paths)


def theme_mock(name='example-theme'):
    """Get a mock representing a theme object.

    :param name: a name of a theme represented by the mock
    :returns: the mock.
    """
    theme = Mock()
    theme.name = name
    return theme


class Base16ThemeNameMapTest(TestCase):
    """Tests for Base16ThemeNameMap."""

    def setUp(self):
        self.theme_names = 'alpha', 'beta', 'omega'
        self.themes = [theme_mock(t) for t in self.theme_names]
        self.tested = Base16ThemeNameMap(self.themes)

    def test_add_adds_a_theme(self):
        """Test if a theme is added to a theme collection."""
        new_theme = theme_mock()
        self.tested.add(new_theme)

        self.assertIn(new_theme.name, self.tested)
        self.assertEqual(new_theme, self.tested[new_theme.name])

    def test_getitem_returns_a_theme(self):
        """Test if an existing theme is returned."""
        expected = self.themes[0]
        actual = self.tested[self.theme_names[0]]
        self.assertEqual(expected, actual)

    def test_getitem_raises_KeyError(self):
        """Test if the exception is raised for an unknown theme."""
        name = 'unknown-theme'
        with self.assertRaisesRegex(KeyError, name):
            self.tested.__getitem__(name)

    def test_init_raises_DuplicateThemeNameError(self):
        """Test if the exception is raised for a duplicate theme."""
        themes = [theme_mock('duplicate-theme') for _ in range(2)]
        with self.assertRaisesRegex(
            DuplicateThemeNameError,
            'A theme named "duplicate-theme" already exists.'
        ):
            Base16ThemeNameMap(themes)

    def test_add_raises_DuplicateThemeNameError(self):
        """Test if the exception is raised for a duplicate theme."""
        theme = theme_mock('duplicate-theme')
        self.tested.add(theme)
        with self.assertRaisesRegex(
            DuplicateThemeNameError,
            'A theme named "duplicate-theme" already exists.'
        ):
            self.tested.add(theme)

    def test_iter(self):
        """Test if __iter__ returns expected iterator.

        Expected iterator is an iterator that returns themes in an
        expected order.
        """
        expected = list(iter({t.name: t for t in self.themes}))
        actual = list(iter(self.tested))
        self.assertSequenceEqual(expected, actual)

    def test_len(self):
        """Test if the number of items is returned."""
        expected = len(self.themes)
        actual = len(self.tested)
        self.assertEqual(expected, actual)

    def test_sorted_by_name(self):
        """Test if the property returns themes sorted by name."""
        expected = sorted(self.themes, key=lambda t: t.name)
        actual = self.tested.sorted_by_name
        self.assertSequenceEqual(expected, actual)

    @parameterized.expand([
        (True, [Mock()]),
        (False, [])
    ])
    def test_bool_returns(self, expected, themes):
        """Test if the method returns expected value.

        :param expected: the value expected to be returned.
        :param themes: content of a collection for which the function
            returns expected values.
        """
        tested = Base16ThemeNameMap(themes)
        actual = bool(tested)
        assertion = self.assertTrue if expected else self.assertFalse
        assertion(actual)

    def test_from_unique(self):
        """Test if a collection of expected, unique themes is returned."""
        unique_themes = [theme_mock(n) for n in ('first', 'second', 'third')]
        with_duplicates = unique_themes + unique_themes[1:]
        expected = Base16ThemeNameMap(unique_themes)
        actual = Base16ThemeNameMap.from_unique(with_duplicates)
        self.assertEqual(expected, actual)
