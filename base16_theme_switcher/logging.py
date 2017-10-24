# -*- coding: utf-8 -*-
import logging
from logging import handlers
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


def configure_root_logger(log_path, verbose=False):
    """Configure the root logger.

    :param log_path: a path to a file to be used by RotatingFileHandler.
    :param verbose: set the level of the console handler to
        logging.DEBUG if True, otherwise set the level to logging.ERROR.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_level = logging.DEBUG if verbose else logging.ERROR
    console_handler.setLevel(console_level)

    logger.addHandler(console_handler)
    with log_path as path:
        file_handler = handlers.RotatingFileHandler(
            str(path), maxBytes=10*1024*1024, encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
