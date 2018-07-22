#! /usr/bin/python3

import unittest
from mock import MagicMock, Mock
import mockfs


class EducatuXBot(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_error(self):
        print("Testing error()")
        from educatuxbot import error
        import syslog

        debug = MagicMock()
        syslog.openlog = MagicMock()
        syslog.syslog = MagicMock()

        print(" * ASCII")
        message = "testing"
        error(message)
        syslog.openlog.assert_called_with("EducatuXBot")
        syslog.syslog.assert_called_with(syslog.LOG_ERR,
                                         "ERROR: %s" % message)

        print(" * UTF-8")
        message = "tésting ç å üt°f-8"
        error(message)
        syslog.openlog.assert_called_with("EducatuXBot")
        syslog.syslog.assert_called_with(syslog.LOG_ERR,
                                         "ERROR: %s" % message)



    def test_log(self):
        print("Testing log()")
        from educatuxbot import log
        import syslog

        debug = MagicMock()
        syslog.openlog = MagicMock()
        syslog.syslog = MagicMock()

        message = "testing"
        log(message)
        syslog.openlog.assert_called_with("EducatuXBot")
        syslog.syslog.assert_called_with(syslog.LOG_INFO,
                                         message)


    def test_read_configuration(self):
        print("Testing read_configuration()")
        from educatuxbot import TelegramBotInterface
        import sys
        import time
        import os
        import configparser

        fs = mockfs.replace_builtins()
        SESSION = "TELEGRAM"
        fs.add_entries({"configuration.conf" : "[TELEGRAM]\n" + \
            "EDUCATUXBOT = abc:123456\n" + \
            "EDUCATUXBOTADMS = HelioLoureiro\n"})
        sys.exit = MagicMock()
        error = MagicMock()

        print(" * correct configuration")
        cfg = TelegramBotInterface()
        cfg.config_file = "configuration.conf"
        cfg.read_configuration()
        self.assertEqual(cfg.settings["token"], "abc:123456", "Parameter didn't match.")
        self.assertEqual(cfg.settings["botadms"], "HelioLoureiro", "Parameter didn't match.")

    def notest_get_telegram_key(self):
        print("Testing get_telegram_key()")

        from educatuxbot import read_configuration, get_telegram_key
        import os
        import configparser

        fs = mockfs.replace_builtins()
        SESSION = "TELEGRAM"
        fs.add_entries({"configuration.conf" : "[TELEGRAM]\n" + \
            "STALLBOT = abc:123456\n" + \
            "STALLBOTADM = HelioLoureiro\n"})
        sys = Mock()
        error = Mock()
        debug = Mock()

        cfg = read_configuration("configuration.conf")
        print(" * testing existent values")
        result = get_telegram_key(cfg, "STALLBOT")
        self.assertEqual(result, "abc:123456", "Resulting is mismatching expected value.")

        print(" * testing non-existent values")
        result = get_telegram_key(cfg, "ROCKNROLL")
        self.assertIsNone(result, "Command returned value (expected empty).")

        mockfs.restore_builtins()


if __name__ == '__main__':
    unittest.main()
