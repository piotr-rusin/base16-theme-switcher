# -*- coding: utf-8 -*-

import logging
import unittest
from unittest.mock import Mock, MagicMock, patch

from parameterized import parameterized

from base16_theme_switcher.logging import NotifySendHandler


class NotifySendHandlerTest(unittest.TestCase):
    """Tests for NotifySendHandler class."""

    def setUp(self):
        self.subprocess_call_patcher = patch(
            'base16_theme_switcher.logging.subprocess.call'
        )
        self.subprocess_call_patch = self.subprocess_call_patcher.start()

    def tearDown(self):
        self.subprocess_call_patcher.stop()

    @parameterized.expand([
        ('normal', logging.INFO),
        ('critical', logging.INFO + 1)
    ])
    def test_emit_calls_expected_command_with_urgency_lvl(
            self, urgency_level, levelno
    ):
        """Test if the method executes an expected command.

        :param urgency_level: expected value of -u (--urgency-level)
            option of the command.
        :param levelno: a number representing a level of log record to
            be emited.
        """
        record_mock = Mock()
        record_mock.levelno = levelno
        msg = 'Test message'
        record_mock.getMessage.return_value = msg

        expected_command = (
            'notify-send -u "{}" "Base16 Theme Switcher" "{}"'.format(
                urgency_level, msg)
        )

        tested = NotifySendHandler()
        tested.emit(record_mock)

        self.subprocess_call_patch.assert_called_once_with(
            expected_command,
            shell=True
        )
