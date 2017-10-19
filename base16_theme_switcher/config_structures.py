# -*- coding: utf-8 -*-
from collections.abc import Mapping, MutableMapping
from pathlib import Path


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
    def from_path_str(cls, path):
        """Create a new configured absolute path.

        :param path: an object representing the path, acceptable as an
            argument of pathlib.Path.
        :returns: a new instance of the class.
        """
        return cls(Path(path))
