# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock, Mock

from parameterized import parameterized

from base16_theme_switcher.config_structures import (
    ConfigKeyError,
    ConfigMapping,
    ConfiguredAbsolutePath,
    ConfiguredFileNotFoundError,
    ConfiguredPathError,
    RootConfigMapping,
)


def get_by_key_chain(mapping, keys):
    """Get a value from nested mapping by a chain of keys.

    :param mapping: the mapping from which the value is extracted.
    :param keys: a sequence of keys used to locate the requested value.
    :returns: a value resulting from getting a value from the mapping by
        the first key and from getting values from nested mappings by
        remaining keys (if there are more than one).
    """
    selection = mapping
    for k in keys:
        selection = selection[k]
    return selection


class ConfigMappingTest(unittest.TestCase):
    """Tests for ConfigMapping class."""

    def prepareData(self):
        """Prepare underlying data for the instance of tested class."""
        self.data = {
            'first': 123,
            'second': 'abc',
            'third': {
                'third.first': 777,
                'third.second': 'pp'
            }
        }

    def setUp(self):
        """Prepare the instance of the class to be used in tests."""
        self.prepareData()
        self.tested = ConfigMapping(self.data, ('root', ))

    @parameterized.expand([
        ('option_value', 'first'),
        ('section', 'third'),
        ('option_value_in_section', 'third', 'third.first')
    ])
    def test_getitem_returns_expected(self, _, *keys):
        """Test if the method returns an expected result.

        :param keys: a chain of keys to be used to access expected and
            actual results.
        """
        expected = get_by_key_chain(self.data, keys)
        actual = get_by_key_chain(self.tested, keys)
        self.assertEqual(expected, actual)

    @parameterized.expand([
        ('key', 'fifth'),
        ('key_in_section', 'third', 'fifth')
    ])
    def test_getitem_raises_ConfigKeyError_for_missing(self, _, *keys):
        """Test if the method raises the exception.

        :param keys: a chain of keys to be used to attempt to access a
            non-existing value.
        """
        with self.assertRaises(ConfigKeyError) as ex:
            get_by_key_chain(self.tested, keys)
            self.assertEqual(
                str(ex),
                'The expected configuration option "{}" is missing '
                'in {}'.format(
                    keys[-1], ':'.join(['root'] + list(keys[:-1]))
                )
            )

    @parameterized.expand([
        ('an_option_value', 'option', 1345),
        ('a_subsection', 'section', {'option': 44})
    ])
    def test_setitem_adds(self, _, key, value):
        """Test if the method adds expected data.

        :param key: a key to be used to index a new value.
        :param value: a value to be added to the mapping.
        """
        self.tested[key] = value
        self.assertEqual(value, self.tested[key])

    @parameterized.expand([
        ('an_option_value', 'first'),
        ('a_subsection', 'third')
    ])
    def test_delitem_deletes(self, _, key):
        """Test if the method deletes data.

        :param key: a key of a value to be deleted from the mapping.
        """
        del self.tested[key]
        self.assertNotIn(key, self.tested)

    def test_len(self):
        """Test if the number of items in the mapping is returned."""
        expected = len(self.data)
        actual = len(self.tested)
        self.assertEqual(expected, actual)

    def test_iter(self):
        """Test the content and ordering of items in the iterator."""
        expected = list(iter(self.data))
        actual = list(iter(self.tested))
        self.assertEqual(expected, actual)


class RootConfigMappingTest(ConfigMappingTest):
    """Tests for RootConfigMapping class."""

    def setUp(self):
        """Prepare the instance of the class to be tested."""
        self.prepareData()
        source = Mock()
        source.read.return_value = self.data
        self.tested = RootConfigMapping(source)


class ConfiguredAbsolutePathTest(unittest.TestCase):
    """Tests for ConfiguredAbsolutePath class."""

    CLASS_UNDER_TEST = ConfiguredAbsolutePath

    def test_str(self):
        """Test if the correct path is returned as a string."""
        expected = '/expected/string/path'

        path = Mock()
        internal_path = MagicMock()
        path.expanduser().absolute.return_value = internal_path
        internal_path.__str__.return_value = expected

        tested = self.CLASS_UNDER_TEST(path)
        expected = '/expected/string/path'
        actual = str(tested)
        self.assertEqual(expected, actual)

    @parameterized.expand([
        (FileNotFoundError, ConfiguredFileNotFoundError),
        (OSError, ConfiguredPathError)
    ])
    def test_context_manager_handles(
            self, handled_exception, raised_exception
    ):
        """Test if the exception is handled.

        :param handled_exception: an exception expected to be handled
            by the context manager.
        :param raised_exception: an exception expected to be raised
            while handling handled_exception.
        """
        tested = self.CLASS_UNDER_TEST(Mock())
        with self.assertRaises(raised_exception):
            with tested:
                raise handled_exception()
