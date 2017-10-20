# -*- coding: utf-8 -*-
import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping, MutableMapping
from pathlib import Path

import configobj
from ruamel.yaml import YAML


class SetupError(Exception):
    """An error in application setup.

    This exception and its subclasses are to be raised when an error in
    configuration file or command line options was detected, or when
    another exception may be a result of such an error.
    """


class ConfigKeyError(SetupError, KeyError):
    """A value of a missing configuration option was requested."""


class ConfiguredPathError(SetupError, OSError):
    """A system error occured when processing a user-provided path."""


class ConfiguredFileNotFoundError(SetupError, FileNotFoundError):
    """A file provided by a user wasn't found or couldn't be created."""


class ConfigMapping(MutableMapping):
    """A multidimensional mapping of configuration options.

    Each key is either a name of an option and is mapped to the option's value,
    or a name of a section of the configuration and is mapped to a mapping
    representing the contents of the section.
    """

    def __init__(self, data, ancestors):
        """Create a configuration mapping.

        :param data: a mapping containing configuration data
        :param ancestors: the list of identifiers used to locate the mapping.
            They can include names of all the parent sections of the given
            configuration mapping or a name of a source of configuration data.
        """
        self._data = data
        self._ancestors = ancestors

    def __getitem__(self, key):
        """Get a value mapped to the given key.

        :param key: a key used to locate the requested value. It can be
            a name of a configuration option or of a section of configuration.
        :returns: a value of a configuration option or a subset of
            configuration options. If the subset is being returned, it
            is wrapped in a new instance of the ConfigMapping class.
        :raises ConfigKeyError: if there is no option value or a subsection
            of the config associated with the given key.
        """
        try:
            value = self._data[key]
        except KeyError:
            raise ConfigKeyError(
                'A requested configuration option "{}" is missing in {}'
                ''.format(key, ':'.join(self._ancestors))
            )

        if (isinstance(value, Mapping) and not
                isinstance(value, self.__class__)):
            value = ConfigMapping(value, self._ancestors + (key,))
        return value

    def __setitem__(self, key, value):
        """Assign a config subcestion or option value to a given name.

        :param key: a name of a config section or option
        :param value: a value of a configuration option or contents of
            a section to be assigned to the given key.
        """
        self._data[key] = value

    def __delitem__(self, key):
        """Remove a config option or a section with a given name.

        :param key: a name of an option or section to be removed.
        """
        del self._data[key]

    def __iter__(self):
        """Iterate on the names of config options or subsections.

        :returns: an iterator object
        """
        return iter(self._data)

    def __len__(self):
        """Get the number of option and section names in the config.

        :returns: the total number of option and section names.
        """
        return len(self._data)


class RootConfigMapping(ConfigMapping):
    """Represents a configuration mapping with a source or destination."""

    def __init__(self, source):
        """Create a new root config mapping.

        :param source: an object to be used as a source of the configuration
        data and a destination to which the changes to the data can be saved.
        """
        self._source = source
        data = source.read(fallback_to_empty=True)
        super().__init__(data, (str(source), ))

    def save(self):
        """Save the configuration data to its destination."""
        self._source.write(self._data)


class ConfiguredAbsolutePath:
    """A path used in the setup process of the application.

    This class encapsulates common operations for paths used in the setup
    phase of the application, like expanding a user directory, making
    the path absolute and handling some errors that might occur while using
    it.
    """

    def __init__(self, path):
        """Create a new configured absolute path.

        :param path: a path object
        """
        self._path = path.expanduser().absolute()

    def __str__(self):
        """Get the path as a string.

        :returns: the path string.
        """
        return str(self._path)

    def __enter__(self):
        """Enter the context manager associated with this path.

        The context manager is responsible for wrapping the expected errors
        that might be raised from the methods of the path object in
        application-specific exception classes. This allows for telling them
        apart from unexpected errors and handling them differently.

        :returns: the internal path object used by the instance.
        """
        return self._path

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the context manager and handle the error.

        The error is handled by checking its type and, depending on it,
        re-raising the error as an exception of another type.

        :raises ConfiguredFileNotFoundError: if the error is FileNotFound
        :raises ConfiguredPathError: if the error is OSError
        :returns: True if there are no errors, False otherwise.
        """
        if exc_type is FileNotFoundError:
            raise ConfiguredFileNotFoundError(exc_value)
        elif exc_type is OSError:
            raise ConfiguredPathError(exc_value)
        return exc_value is None

    @classmethod
    def from_(cls, path):
        """Create a new configured absolute path.

        :param path: an object representing the path, acceptable as an
            argument of pathlib.Path.
        :returns: a new instance of the class.
        """
        return cls(Path(path))


class LazilySaveablePath(ConfiguredAbsolutePath, ABC):
    """A path read during application setup.

    The path may not point to an existing file, but might still be used
    to save new data.

    The saving is performed lazily - for details, see
    LazilySaveablePath.write.
    """

    def __init__(self, path):
        """Get a path to a lazily-saveable file.

        :param path: a path object
        :param target_must_exist: a boolean value specifying if the
            target of the path has to exist. If it doesn't have to,
            reading data from the file will return an empty value.
            Otherwise it will result in an error.
        """
        super().__init__(path)
        self._logger = logging.getLogger(__name__)

    def read(self, fallback_to_empty=False):
        """Get the data from the path.

        :param fallback_to_empty: fallback to a default empty value
            provided by the subclass if the file under the path doesn't
            exist.
        :returns: data read from an existing file, or a default empty
            value if the file doesn't exist yet and wasn't necessary.
        :raises ConfiguredFileNotFoundError: if the file is required, but
            it doesn't exist.
        :raises ConfiguredPathError: if an operating system error occurs
            during the operation.
        """
        self._logger.info('Reading configuration from %s', self._path)
        try:
            with self:
                return self._do_read()
        except ConfiguredFileNotFoundError:
            if not fallback_to_empty:
                raise
            self._logger.info(
                '%s doesn\'t exist yet. Returning the default empty value'
            )
            return self._get_empty_data()

    @abstractmethod
    def _do_read(self):
        return

    @abstractmethod
    def _get_empty_data(self):
        return

    def write(self, data):
        """Save given data to the file under the path.

        The data is saved lazily, that is: it is saved only if the data
        is not empty or if the file already exists. If the file doesn't
        exist and the data is empty, we don't have to create a file to
        reflect a lack of custom configuration data.

        :param data: data to be saved
        :raises ConfiguredFileNotFoundError: if the parent path doesn't
            exist.
        :raises ConfiguredPathError: if an operating system error occurs
            during the operation.
        """
        if not (data or self._path.exists()):
            return
        self._logger.info('Saving configuration to %s', self._path)

        try:
            with self:
                self._do_write(data)
        except ConfiguredFileNotFoundError:
            raise ConfiguredFileNotFoundError(
                'Parent dir doesn\'t exist for file: {}'.format(self._path)
            )

    @abstractmethod
    def _do_write(self, data):
        pass


class LazilySaveableMappingPath(LazilySaveablePath):
    """A path to a lazily saveable file containing a mapping."""

    _get_empty_data = dict

    @classmethod
    def get_config_mapping(cls, path):
        """Get config mapping from path.

        :param path: a path pointing to a file of a type supported by
            this class.
        :param target_must_exist: a boolean value specifying if the
            target of the path has to exist. If it doesn't have to,
            reading data from the file will return an empty value.
            Otherwise it will result in an error.
        :returns: the configuration mapping using the file as a source
            or destination for its data.
        """
        return RootConfigMapping(cls.from_(path))


class YamlConfigPath(LazilySaveableMappingPath):
    """A path to a YAML file."""

    _LOADER = YAML()

    def _do_read(self):
        return self._LOADER.load(self._path)

    def _do_write(self, data):
        self._LOADER.dump(data, self._path)


class CfgConfigPath(LazilySaveableMappingPath):
    """A path to an ini-type file."""

    _get_empty_data = configobj.ConfigObj

    def _do_read(self):
        return configobj.ConfigObj(str(self._path))

    def _do_write(self, data):
        self._data.write()


class TextConfigPath(LazilySaveablePath):
    """A path to a config treated as an ordinary text file."""

    _get_empty_data = str

    def _do_read(self):
        return self._path.read_text()

    def _do_write(self, data):
        self._path.write_text(data)
