# -*- coding: utf-8 -*-
import importlib
import logging
import pkgutil


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
