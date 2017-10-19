# -*- coding: utf-8 -*-


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
