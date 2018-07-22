#! /usr/bin/python3 -u
# -*- coding: utf-8 -*-

BOTNAME = "EducatuX"

import os
import sys
import configparser
import time
import syslog
import telebot
from datetime import date

# pyTelegramBotAPI
# https://github.com/eternnoir/pyTelegramBotAPI
# pip3 install pyTelegramBotAPI


__version__ = "Fri Jul  6 13:23:35 CEST 2018"

START_TIME = time.ctime()


# Message to send to @BotFather about its usage.
Commands_Listing = """

Open a talk to @BotFather and send these commands
using "/setcommands"

== EducatuX Bot ==

"""

DEBUG = False
CONFIG = ".educatuxbotrc"


RESPONSES_TEXT = {
    "/start" : "Bem-vindo ao jogo de perguntas e repostas do EducatuX",
    "/jogar" :  "Iniciando o jogo"
    }

### Refactoring
def debug(msg):
    if DEBUG or "DEBUG" in os.environ and msg:
        try:
            print("[%s] %s" % (time.ctime(), msg))
        except Exception as e:
            print("[%s] DEBUG ERROR: %s" % (time.ctime(), e))

def error(message):
    """Error handling for logs"""
    errormsg = u"ERROR: %s" % message
    debug(errormsg)
    syslog.openlog("%sBot" % BOTNAME)
    syslog.syslog(syslog.LOG_ERR, errormsg)


def log(message):
    """Syslog handling for logs"""
    infomsg = u"%s" % message
    debug(infomsg)
    syslog.openlog("%sBot" % BOTNAME)
    syslog.syslog(syslog.LOG_INFO, infomsg)

class TelegramBotInterface:
    def __init__(self):
        debug("TelegramBotInterface settings init")
        self.HOME = os.environ.get('HOME')
        self.PIDFILE = "%s/.educatux.pid" % self.HOME
        self.settings = {
            'config_section' : "TELEGRAM",
            'botadms' : [],
            'token' : None
            }

        self.config_file = "%s/%s" % (self.HOME, CONFIG)

    def check_if_run(self):
        pid = self.read_file(self.PIDFILE)
        current_pid = os.getpid()
        if pid is None:
            return
        try:
            pid_t = int(pid.rstrip())
        except ValueError:
            pid_t = 0
        debug("pid=%s" % pid)
        if pid_t > 0 and pid_t != current_pid:
            if os.path.exists("/proc/%d" % pid_t):
                log("[%s] Already running - keepalive done." % time.ctime())
                sys.exit(os.EX_OK)


    def read_configuration(self):
        """ Read configuration file and return object
        with config attributes"""
        cfg = configparser.ConfigParser()
        debug("Reading configuration: %s" % self.config_file)
        if not os.path.exists(self.config_file):
            error("Failed to find configuration file %s" % self.config_file)
            sys.exit(os.EX_CONFIG)
        with open(self.config_file) as fd:
            cfg.read_file(fd)
        self.settings["token"] = cfg.get(self.settings["config_section"], "EDUCATUXBOT")
        adms = cfg.get(self.settings["config_section"], "EDUCATUXBOTADMS")
        if type(adms) == type(str()):
            self.settings["botadms"].append(adms)
        else:
            self.settings["botadms"] = adms

    def get_answer(self, question):
        """ Search for a response from dictionary """
        if question.lower() in RESPONSES_TEXT:
            return RESPONSES_TEXT[question.lower()]
        return None


    def reply_text(self, obj, session, text):
        """ Generic interface to answer """
        try:
            obj.reply_to(session, text)
        except Exception as e:
            error("%s" % e)

    def main(self):
        """Main settings"""
        self.check_if_run()
        self.save_file("%d\n" % os.getpid(), self.PIDFILE)

    def save_file(self, message, filename):
        with open(filename, 'w') as destination:
            destination.write("%s" % message)

    def read_file(self, filename):
        if not os.path.exists(filename):
            return None
        return open(filename).read()

botintf = TelegramBotInterface()
botintf.read_configuration()
botintf.main()
token = botintf.settings["token"]
bot = telebot.TeleBot(token)

def main():
    debug("polling for enquiries")
    bot.polling()

### Bot callbacks below ###
@bot.message_handler(func=lambda m: True)
def Talking(session):
    debug(session.text)
    if botintf.get_answer(session.text):
        botintf.reply_text(bot, session, botintf.get_answer(session.text))
        return


if __name__ == '__main__':
    main()
