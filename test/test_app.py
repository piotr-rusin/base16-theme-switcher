# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock, MagicMock

from parameterized import parameterized

from base16_theme_switcher.app import (
    ConfigValueError,
    SetupError,
    ThemeApplier,
    ThemeSwitcherBuilder,
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
