# -*- coding: utf-8 -*-
"""Components of plugin discovery and loading system."""

import importlib
import logging
import pkgutil

from .config_structures import ConfigValueError, SetupError


def get_modules_by_name_prefix(prefix):
    """Get modules whose name starts with the prefix.

    :param prefix: a prefix used to select modules to be returned.
    :returns: a map of the modules to their names, with the prefix
        stripped.
    """
    logger = logging.getLogger(__name__)

    name_module_map = {}
    for _, module_name, _ in pkgutil.iter_modules():
        if not module_name.startswith(prefix):
            continue
        try:
            module = importlib.import_module(module_name)
            name_module_map[module_name[len(prefix):]] = module
            logger.info('Successfully imported "%s" module.', module_name)
        except ImportError:
            logger.exception(
                'A module "%s" was found, but couldn\'t be imported',
                module_name
            )

    return name_module_map


def apply_configured_plugins(plugin_api_impl, available_plugins):
    """Apply configured plugins to the application.

    :param plugin_api_impl: an object providing an application-specific
        part of plugin system API. It also provides a sequence of names
        of plugins to be activated.
    :param available_plugins: a mapping of available plugins to their
        names.
    :raises ConfigValueError: if an unavailable plugin is included in
        the names of plugins to be activated, or if this error was
        raised while applying a plugin.
    :raises SetupError: if there was an error with setting up a plugin.
    """
    logger = logging.getLogger(__name__)

    for name in plugin_api_impl.plugins_to_activate:
        logger.info('Attemtping to initialize "%s" plugin...')
        try:
            module = available_plugins[name]
        except KeyError:
            raise ConfigValueError(
                'The "{}" plugin is configured but not available.'.format(name)
            )
        try:
            module.apply_to(plugin_api_impl)
        except SetupError as e:
            raise SetupError(
                'Error while setting up "{}" plugin.'.format(name)
            ) from e
        logger.info('The "%s" plugin was successfully initialized.', name)


def apply_configured_prefixed_plugins(plugin_api_impl, prefix):
    """Apply configured plugins available as modules.

    :param plugin_api_impl: an object providing an application-specific
        part of plugin system API. It also provides a sequence of names
        of plugins to be activated.
    :param prefix: a prefix of names of plugin modules to be recognized
        as available.
    :raises ConfigValueError: if an unavailable plugin is configured, or
        if this error was raised while applying a plugin.
    :raises SetupError: if there was an error in setting up a plugin.
    """
    plugin_name_map = get_modules_by_name_prefix(prefix)
    apply_configured_plugins(plugin_api_impl, plugin_name_map)
