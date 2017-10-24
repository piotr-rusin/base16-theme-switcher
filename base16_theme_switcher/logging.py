# -*- coding: utf-8 -*-
import logging
import subprocess


class NotifySendHandler(logging.Handler):
    """A handler showing messages as desktop notifications."""

    def emit(self, record):
        """Show the message in the record.

        The message is shown using notify-send command provided by
        libnotify package.

        :param record: a log record containing a message to be displayed.
        """
        urgency_level = (
            'normal' if record.levelno <= logging.INFO else 'critical'
        )

        subprocess.call(
            'notify-send -u "{}" "Base16 Theme Switcher" "{}"'
            ''.format(urgency_level, record.getMessage()),
            shell=True
        )
