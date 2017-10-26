# -*- coding: utf-8 -*-
"""Tests for components of plugin discovery and loading system."""

from random import shuffle
from unittest import TestCase
from unittest.mock import Mock, patch

from parameterized import parameterized

from base16_theme_switcher.plugin_loading import (
    ConfigValueError,
    SetupError,
    apply_configured_plugins,
    get_modules_by_name_prefix,
)


def get_prefixed(strs, prefix):
    """Get all string values with a prefix applied to them.

    :param strs: a sequence of strings to be given a prefix.
    :param prefix: a prefix to be added to the strings
    :returns: a list of prefixed strings
    """
    return [prefix + n for n in strs]


class GetModulesByNamePrefixTest(TestCase):
    """Tests for get_modules_by_name_prefix function."""

    PREFIX = 'pref_'
    PLUGIN_NAMES = ['lorem', 'ipsum', 'dolor']
    PLUGIN_MODULE_NAMES = get_prefixed(PLUGIN_NAMES, PREFIX)
    MODULE_NAMES = ['abc', 'flask', 'sqlalchemy'] + PLUGIN_MODULE_NAMES
    shuffle(MODULE_NAMES)


    def setUp(self):
        self.pkgutil_patcher = patch(
            'base16_theme_switcher.plugin_loading.pkgutil'
        )
        self.pkgutil_mock = self.pkgutil_patcher.start()
        self.pkgutil_mock.iter_modules.return_value = (
            [Mock(), m, Mock()] for m in self.MODULE_NAMES
        )

        self.importlib_patcher = patch(
            'base16_theme_switcher.plugin_loading.importlib'
        )
        self.importlib_mock = self.importlib_patcher.start()

    def tearDown(self):
        self.pkgutil_patcher.stop()
        self.importlib_patcher.stop()

    @parameterized.expand([
        ('without_errors'),
        ('with_one_error', [PLUGIN_NAMES[1]]),
        ('with_two_errors', PLUGIN_NAMES[1:])
    ])
    def test_gets_expected_module_map(self, _, error_triggers=()):
        """Test if a map of expected plugin modules is returned.

        :param error_triggers: names of plugins provided by modules whose
            import triggers ImportError.
        """
        unimportable_modules = get_prefixed(error_triggers, self.PREFIX)

        def import_module(name):
            if name in unimportable_modules:
                raise ImportError()
            return Mock()

        self.importlib_mock.import_module.side_effect = import_module

        expected = [p for p in self.PLUGIN_NAMES if p not in error_triggers]
        module_to_name_map = get_modules_by_name_prefix(self.PREFIX)

        self.assertCountEqual(expected, module_to_name_map.keys())


class ApplyConfiguredPluginsTest(TestCase):
    """Tests for apply_configured_plugins function."""

    def setUp(self):
        self.plugin_api_impl_mock = Mock()
        plugins_to_activate = ['first', 'second', 'third']
        self.available_plugin_mocks = {
            n: Mock() for n in plugins_to_activate
        }
        self.plugin_api_impl_mock.plugins_to_activate = plugins_to_activate
        self.plugins_to_activate = plugins_to_activate

    def _call(self):
        apply_configured_plugins(
            self.plugin_api_impl_mock,
            self.available_plugin_mocks
        )

    def assertCallRaises(self, exc_type, msg_regex):
        """Check if the call to the function raises an error.

        :param exc_type: a type of an exception to be raised.
        :param msg_regex: a regular expression expected to match the string
            representation of expected error.
        """
        with self.assertRaisesRegex(exc_type, msg_regex):
            self._call()

    def test_raises_ConfigValueError_2(self):
        """Check if the error is raised for unavailable plugin."""
        self.plugins_to_activate.append('unknown_plugin')
        msg = 'The "unknown_plugin" plugin is configured but not available.'
        self.assertCallRaises(ConfigValueError, msg)

    def test_raises_SetupError(self):
        """Check if the error is re-raised while applying a plugin."""
        name, mock = list(self.available_plugin_mocks.items())[1]
        mock.apply_to.side_effect = SetupError
        msg = 'Error while setting up "{}" plugin.'.format(name)
        self.assertCallRaises(SetupError, msg)

    def test_applies_all(self):
        """Check if the function applies all plugins to the object."""
        self._call()
        for m in self.available_plugin_mocks.values():
            m.apply_to.assert_called_once_with(self.plugin_api_impl_mock)
