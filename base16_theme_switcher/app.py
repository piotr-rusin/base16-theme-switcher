# -*- coding: utf-8 -*-
import logging
import subprocess
from abc import ABC, abstractmethod

from .config_structures import ConfigValueError, SetupError, YamlConfigPath
from .themes import Base16ThemeNameMap


class ThemeApplier(ABC):
    """A color theme applier for third party applications.

    Subclasses of this class are responsible for providing a support for
    base16 theme setting for applications accepting color configuration.
    """

    @abstractmethod
    def apply(self, theme):
        """Perform actions necessary to apply the theme.

        The actions are supposed to include everything that must and
        can be done for the theme-switching operation to affect the
        application supported by this theme applier.

        :param theme: a theme to be set.
        """
        pass

    @classmethod
    def __subclasshook__(cls, C):
        if cls is ThemeApplier:
            if any('apply' in B.__dict__ for B in C.__mro__):
                return True
        return NotImplemented


class ThemeSwitcherBuilder:
    """A class responsible for building a valid application object.

    The builder pattern is being used because this way constructing
    a valid application object may be split between several plugins,
    and because a builder object can expose properties representing
    pluggable components to plugins.
    """

    def __init__(self, config, themes):
        """Create a new instance.

        :param config: a configuration mapping to be used by the theme
            switcher.
        :param themes: a mapping of themes indexed by their names.
        """
        self._config = config
        if not themes:
            raise SetupError('The themes mapping cannot be empty.')
        self._themes = themes
        self._theme_appliers = []
        self._prompt = None

    @property
    def config(self):
        """Configuration mapping to be used by theme switcher."""
        return self._config

    def add_theme_applier(self, theme_applier):
        """Add a theme applier to be used by the theme switcher.

        :param theme_applier: the theme applier to be added.
        :raises TypeError: if the theme applier object doesn't provide
            apply method.
        """
        if not isinstance(theme_applier, ThemeApplier):
            raise TypeError(
                '{} is not an instance of {}'.format(
                    theme_applier, ThemeApplier)
            )
        self._components.append(theme_applier)

    @property
    def prompt(self):
        """Get theme prompt to be used by the theme switcher."""
        return self._prompt

    @prompt.setter
    def prompt(self, value):
        """Set a callable theme prompt for the theme switcher.

        :param value: a callable to be used as the prompt.
        :raises SetupError: if a caller attempts to override an already
            set prompt.
        :raises TypeError: if the value is not callable.
        """
        if self._prompt is not None:
            raise SetupError('Only one plugin may provide a prompt.')

        if not callable(value):
            raise TypeError('The prompt must be callable.')
        self._prompt = value

    def build(self):
        """Get theme switcher object.

        :returns: the theme switcher object.
        """
        return ThemeSwitcher(
            config=self._config,
            themes=self._themes,
            theme_appliers=self._components,
            prompt=self._prompt
        )

    @classmethod
    def from_(cls, config_path):
        """Create a new instance using application config file.

        :param config_path: a path to YAML file containing configuration
            to be used by theme switcher.
        :raises ConfigValueError: if the theme directory provided in
            the configuration doesn't contain any themes.
        """
        config = YamlConfigPath.get_config_mapping(config_path)
        themes = Base16ThemeNameMap.from_unique_in(
            config['theme-search-dir-path']
        )
        if not themes:
            raise ConfigValueError(
                'There are no themes in {}.'.format(
                    config['theme-search-dir-path']
                )
            )
        return cls(config, themes)


class ThemeSwitcher:
    """An object responsible for setting themes."""

    def __init__(self, config, themes, theme_appliers, prompt):
        """Create a new instance.

        :param config: a configuration mapping to be used by the object.
        :param themes: a mapping of themes indexed by their names.
        :param theme_appliers: a sequence of objects responsible for
            applying theme changes to different applications.
        :param prompt: a callable for presenting user with a theme
            selection prompt.
        """
        if config is None:
            raise SetupError(
                'No configuration provided to theme switcher.'
            )
        self._config = config
        if not themes:
            raise SetupError('No themes provided to theme switcher.')
        self._themes = themes
        self._theme_appliers = theme_appliers
        if prompt is None:
            raise SetupError('No prompt provided to theme switcher.')
        self._prompt = prompt
        self._logger = logging.getLogger(__name__)

    def _apply(self, theme_name):
        """Apply a theme without saving it to the configuration.

        :param theme_name: a name of a theme to be applied.
        :raises KeyError: if there is no theme with the name.
        """
        theme = self._themes[theme_name]
        subprocess.call('xrdb -merge {}'.format(theme), shell=True)
        for c in self._theme_appliers:
            c.apply(theme)

    @property
    def current_theme_name(self):
        """Get a name of the currently configured theme."""
        return self._config.get(
            'theme',
            self._themes.sorted_by_name[0].name
        )

    @current_theme_name.setter
    def current_theme_name(self, theme_name):
        """Set a theme with given name.

        The process consists of applying the theme and saving its name
        to the configuration.

        :param theme_name: a name of a theme to be set.
        :raises KeyError: if there is no theme with the name.
        """
        self._apply(theme_name)
        self._config['theme'] = theme_name
        self._config.save()
        self._logger.info(
            'The theme "%s" has been successfully applied.', theme_name
        )

    def reload(self):
        """Re-apply the currently configured theme."""
        self._logger.info('Reloading a preconfigured theme...')
        self._apply(self.current_theme_name)
        self._logger.info(
            'The theme "%s" has been reloaded successfully.',
            self.current_theme_name
        )

    def main(self, command_args):
        """Set or apply a theme based on command-line arguments.

        :param command_args: command-line arguments.
        """
        if command_args.reload:
            self.reload()
            return

        theme = command_args.theme
        if theme is None:
            theme = self._prompt()

        self.current_theme_name = theme
