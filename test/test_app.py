# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock, MagicMock, patch

from parameterized import parameterized

from base16_theme_switcher.app import (
    ConfigValueError,
    SetupError,
    ThemeApplier,
    ThemeSwitcher,
    ThemeSwitcherBuilder
)


class ThemeSwitcherBuilderTest(unittest.TestCase):
    """Tests for ThemeSwitcherBuilder class."""

    def setUp(self):
        self.config_mock = MagicMock()
        self.themes_mock = MagicMock()
        self.tested = ThemeSwitcherBuilder(
            self.config_mock,
            self.themes_mock
        )

    def test_init_raises_SetupError(self):
        """Test if empty themes parameter triggers the error."""
        with self.assertRaisesRegex(
            SetupError, 'The themes mapping cannot be empty.'
        ):
            ThemeSwitcherBuilder(self.config_mock, {})

    def test_add_theme_applier_raises_TypeError(self):
        """Test non-ThemeApplier parameter triggers the error."""
        not_applier = Mock()
        with self.assertRaisesRegex(
            TypeError,
            '{} is not an instance of {}'.format(not_applier, ThemeApplier)
        ):
            self.tested.add_theme_applier(not_applier)

    def test_prompt_setter_raises_SetupError(self):
        """Test if re-assigning a prompt triggers the error."""
        self.tested.prompt = Mock()
        with self.assertRaisesRegex(
            SetupError,
            'Only one plugin may provide a prompt.'
        ):
            self.tested.prompt = Mock()

    def test_prompt_setter_raises_TypeError(self):
        """Test if non-callable parameter triggers the error."""
        with self.assertRaisesRegex(
            TypeError,
            'The prompt must be callable.'
        ):
            self.tested.prompt = None

    @patch('base16_theme_switcher.app.YamlConfigPath')
    @patch('base16_theme_switcher.app.Base16ThemeNameMap')
    def test_from_raises_ConfigValueError(self, b16tnm_class, ycp_class):
        """Test if the error occurs when no themes are found."""
        theme_dir = '/home/example/.base16_themes'
        ycp_class.get_config_mapping.return_value = {
            'theme-search-dir-path': theme_dir
        }
        b16tnm_class.from_unique_in.return_value = []

        with self.assertRaisesRegex(
            ConfigValueError,
            'There are no themes in {}.'.format(theme_dir)
        ):
            ThemeSwitcherBuilder.from_('/home/example/.config/b16ts/conf.yaml')


def theme_mock(name):
    """Get a mock object representing a theme.

    :param name: a name of a theme.
    """
    theme = Mock()
    theme.name = name
    return theme


def get_command_args_mock(theme_name):
    """Get a mock of command-line argument object.

    The function assumes the reload attribute equal to False -
    otherwise we could just use an unaltered instance of Mock.

    :param _reload: a value of reload attribute of command_args.
    :param theme_name: a name of a theme to be set, provided by
        command_args.
    """
    command_args = Mock()
    command_args.reload = False
    command_args.theme = theme_name

    return command_args


class ThemeSwitcherTest(unittest.TestCase):
    """Tests for ThemeSwitcher class."""

    def setUp(self):
        theme_names = 'first', 'second', 'third'
        self.themes = [theme_mock(n) for n in theme_names]
        name_to_theme = {t.name: t for t in self.themes}
        themes_param_mock = MagicMock()
        themes_param_mock.__getitem__.side_effect = name_to_theme.__getitem__
        themes_param_mock.sorted_by_name = [
            name_to_theme[n] for n in theme_names
        ]

        self.config = {'theme': theme_names[0]}
        self.config_mock = MagicMock()
        self.config_mock.__getitem__.side_effect = self.config.__getitem__
        self.config_mock.get.side_effect = self.config.get

        self.theme_applier_mocks = [Mock() for _ in range(3)]
        self.prompt_mock = Mock()
        self.tested = ThemeSwitcher(
            self.config_mock,
            themes_param_mock,
            self.theme_applier_mocks,
            self.prompt_mock
        )

    @parameterized.expand([
        ('configuration', 'config'),
        ('themes', 'themes'),
        ('prompt', 'prompt')
    ])
    def test_init_raises_SetupError_for_no(self, descr, trigger_key):
        """Test if the error is raised for an invalid parameter."""
        kwargs = {
            'config': Mock(),
            'themes': Mock(),
            'theme_appliers': Mock(),
            'prompt': Mock()
        }
        kwargs[trigger_key] = None

        with self.assertRaisesRegex(
            SetupError,
            'No {} provided to theme switcher.'.format(descr)
        ):
            ThemeSwitcher(**kwargs)

    def assert_was_set(self, theme):
        """Assert that the theme was set in configuration.

        :param theme: a theme expected to be set.
        """
        self.config_mock.__setitem__.assert_called_once_with(
            'theme',
            theme.name
        )

    def assert_was_applied(self, theme):
        """Assert that the theme was applied using theme appliers.

        :param theme: a theme expected to be applied.
        """
        for m in self.theme_applier_mocks:
            m.apply.assert_called_once_with(theme)

    @parameterized.expand([
        ('sets_a_theme', assert_was_set),
        ('applies_a_theme', assert_was_applied)
    ])
    def test_current_theme_name_setter(self, _, assertion):
        """Test if current_theme_name property is correctly set."""
        theme = self.themes[0]

        self.tested.current_theme_name = theme.name

        assertion(self, theme)

    def test_current_theme_name_setter_raises_KeyError(self):
        """Test if the error is raised for an unknown theme."""
        name = 'unknown-theme'
        with self.assertRaisesRegex(KeyError, name):
            self.tested.current_theme_name = name

    def _test_reloads_configured_theme(self, command, *args):
        theme = self.themes[1]
        self.config['theme'] = theme.name

        command(*args)

        self.assert_was_applied(theme)

    def test_reload(self):
        """Test if an already set theme is applied."""
        self._test_reloads_configured_theme(self.tested.reload)

    def test_main_reloads_a_theme(self):
        """Test if an already set theme is applied."""
        self._test_reloads_configured_theme(self.tested.main, Mock())

    @parameterized.expand([
        ['sets_theme_from_prompt'],
        ['applies_theme_from_prompt'],
        ['sets_theme_from_cli'],
        ['applies_theme_from_cli']
    ])
    def test_main(self, name_suffix):
        """Test if an inferred assertion based is true.

        :param name_suffix: the suffix applied to the name of this
            function to get the name of the test. This value is also
            used for inferring the assertion made in the test.
        """
        theme = self.themes[0]

        cli_theme = theme.name
        prompt_theme = None
        if name_suffix.endswith('from_prompt'):
            cli_theme = None
            prompt_theme = theme.name
        self.prompt_mock.return_value = prompt_theme
        command_args_mock = get_command_args_mock(cli_theme)

        self.tested.main(command_args_mock)

        assertion = self.assert_was_applied
        if name_suffix.startswith('sets'):
            assertion = self.assert_was_set
        assertion(theme)
