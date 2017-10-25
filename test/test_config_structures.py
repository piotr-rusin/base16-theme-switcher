# -*- coding: utf-8 -*-
"""Tests for classes representing configuration data and sources."""

import unittest
from unittest.mock import MagicMock, Mock

from parameterized import parameterized

from base16_theme_switcher.config_structures import (
    ConfigKeyError,
    ConfigMapping,
    ConfiguredAbsolutePath,
    ConfiguredFileNotFoundError,
    ConfiguredPathError,
    LazilySaveablePath,
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
        self.initial_ancestors = 'root',
        self.tested = ConfigMapping(self.data, self.initial_ancestors)

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
        msg = (
            'A requested configuration option "{}" is missing '
            'in {}'.format(keys[-1], ':'.join(
                self.initial_ancestors + tuple(keys[:-1])
            ))
        )
        with self.assertRaisesRegex(ConfigKeyError, msg):
            get_by_key_chain(self.tested, keys)

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
        source = MagicMock()
        source.__str__.return_value = 'root'
        self.initial_ancestors = str(source),
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


class ConcreteLSPath(LazilySaveablePath):
    """A subclass of LazilySaveablePath to be used in testing.

    LazilySaveablePath is an example of template method pattern. It
    implements most of the functionality expected of its subclasses,
    except for some necessary, subclass-specific details. The methods
    implemented by subclasses are much simpler and contain very little
    code.

    For these reasons, testing will be limited to testing the
    implementation of the parent class. This is achieved by testing a
    special subclass, providing the necessary methods as mocks.
    """

    def __init__(self, path):
        """Create the new instance.

        :param path: a mock object representing a file or directory path.
        """
        super().__init__(path)
        self.internal_path_mock = self._path
        self.do_read_mock = Mock()
        self.do_write_mock = Mock()
        self.get_empty_data_mock = Mock()

    def _do_read(self):
        return self.do_read_mock()

    def _get_empty_data(self):
        return self.get_empty_data_mock()

    def _do_write(self, data):
        self.do_write_mock(data)


class LazilySaveablePathTest(ConfiguredAbsolutePathTest):
    """Tests for LazilySaveablePath class.

    The class under test is actually a subclass of the class to be
    tested. See the docstring of ConcreteLSPath for details.
    """

    CLASS_UNDER_TEST = ConcreteLSPath

    def setUp(self):
        """Prepare an instance of the class to be used in tests."""
        path = Mock()
        self.tested = ConcreteLSPath(path)

    def _test_read_returns(self, source_of_expected, fallback_to_empty):
        """Test if the method returns an expected result.

        :param source_of_expected: a mock representing a method of a
            subclass of the tested class. The method is expected to be
            the one providing the expected return value as its own
            return value.
        :param fallback_to_empty: a value of the fallback_to_empty
            parameter of the tested method.
        """
        expected = Mock()
        source_of_expected.return_value = expected
        actual = self.tested.read(fallback_to_empty)

        self.tested.do_read_mock.assert_called_once_with()
        self.assertEqual(expected, actual)

    @parameterized.expand([
        ('with_fallback', True),
        ('without_fallback', False)
    ])
    def test_read_returns_content(self, _, fallback_to_empty):
        """Test if the method returns content of the path.

        :param fallback_to_empty: a value of the parameter of the tested
            method, with the same name.
        """
        self._test_read_returns(self.tested.do_read_mock, fallback_to_empty)

    def test_read_returns_empty_value(self):
        """Test if the method returns empty value."""
        self.tested.do_read_mock.side_effect = ConfiguredFileNotFoundError
        self._test_read_returns(
            self.tested.get_empty_data_mock,
            fallback_to_empty=True
        )
        self.tested.get_empty_data_mock.assert_called_once_with()

    @parameterized.expand([
        (ConfiguredFileNotFoundError, ),
        (ConfiguredPathError, ),
        (ConfiguredPathError, True)
    ])
    def test_read_raises(self, exception, fallback_to_empty=False):
        """Test if the method raises ConfiguredFileNotFoundError.

        :param exception: an exception expected to be raised.
        :param fallback_to_empty: a value for fallback_to_empty parameter
            of the tested method.
        """
        self.tested.do_read_mock.side_effect = exception

        with self.assertRaises(exception):
            self.tested.read(fallback_to_empty)

        self.tested.do_read_mock.assert_called_once_with()
        self.tested.get_empty_data_mock.assert_not_called()

    @parameterized.expand([
        ('writes_empty_data_to_existing_file', False, True),
        ('does_not_write_empty_data_to_a_non_existing_file', False, False),
        ('writes_data_to_new_file', True, False),
        ('updates_file', True, True),
        (
            'raises_ConfiguredFileNotFoundError',
            True, False, ConfiguredFileNotFoundError
        ),
        (
            'raises_ConfiguredPathError_for_empty_data',
            False, True, ConfiguredPathError
        ),
        (
            'raises_ConfiguredPathError_for_existing_file',
            True, True, ConfiguredPathError
        ),
        (
            'raises_ConfiguredPathError_for_non_existing_file',
            True, False, ConfiguredPathError
        )
    ])
    def test_write(
            self, _, data_not_empty, file_exists, expected_exception=None
    ):
        """Test if the method writes data when it's expected to.

        :param data_not_empty: False if the data mock object represents
            empty data passed to the method, True otherwise.
        :param file_exists: True if the file represented by the path
            exists, False otherwise
        :param expected_exception: a type of the exception expected to
            be raised by the tested method, if any.
        """
        self.tested.internal_path_mock.exists.return_value = file_exists
        data = MagicMock()
        data.__bool__.return_value = data_not_empty

        if expected_exception is not None:
            self.tested.do_write_mock.side_effect = expected_exception
            with self.assertRaises(expected_exception):
                self.tested.write(data)
        else:
            self.tested.write(data)

        if not (data_not_empty or file_exists):
            self.tested.do_write_mock.assert_not_called()
        else:
            self.tested.do_write_mock.assert_called_once_with(data)
