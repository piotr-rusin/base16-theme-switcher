# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod


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
