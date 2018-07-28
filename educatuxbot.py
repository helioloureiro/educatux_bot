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
import pickle

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
/start Mensagem de boas-vindas.
/jogar Inicia o jogo.
"""

DEBUG = False
CONFIG = ".educatuxbotrc"

MISUNDERSTAND = "Comando não reconhecido."
UNSAFE = "/unsafe"
RESPONSES_TEXT = {
    "/start" : "Bem-vindo ao jogo de perguntas e repostas do EducatuX.",
    "/jogar" :  "Iniciando o jogo.",
    "/unsafe" : "Para jogar inicie uma sessão privada com o bot."
    }
COMMANDS = {
    "/reboot" : "os._exit(os.EX_OK)"
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
        self.userdb = "%s/educatux.db" % self.HOME
        self.settings = {
            'config_section' : "TELEGRAM",
            'botadms' : [],
            'token' : None,
            "dbuser" : None,
            "dbhost" : None,
            "dbport" : None,
            "dbpassword" : None
            }
        self.bot = None
        self.config_file = "%s/%s" % (self.HOME, CONFIG)
        self.initialized_shared_memory(dict())


    def check_if_run(self):
        pid = self.read_file(self.PIDFILE)
        current_pid = os.getpid()
        if pid is None:
            return
        try:
            pid_t = int(pid.rstrip())
        except ValueError:
            pid_t = 0
        debug("pid=%d" % pid_t)
        if pid_t > 0 and pid_t != current_pid:
            if os.path.exists("/proc/%d" % pid_t):
                log("[%s] Already running - keepalive done." % time.ctime())
                sys.exit(os.EX_OK)

    def remove_lock(self):
        os.unlink(self.PIDFILE)

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
        self.settings["token"] = cfg.get("TELEGRAM", "EDUCATUXBOT")
        adms = cfg.get("TELEGRAM", "EDUCATUXBOTADMS")
        adms = adms.replace(",", " ")
        for item in adms.split():
            if len(item) > 2:
                self.settings["botadms"].append(item)
        #database settings
        self.settings["dbuser"] = cfg.get("MYSQL", "DBUSER")
        self.settings["dbhost"] = cfg.get("MYSQL", "DBHOST")
        self.settings["dbport"] = cfg.get("MYSQL", "DBPORT")
        self.settings["dbpassword"] = cfg.get("MYSQL", "DBPASSWORD")

    def get_answer(self, question):
        """ Search for a response from dictionary """
        if question.lower() in RESPONSES_TEXT:
            return RESPONSES_TEXT[question.lower()]
        return None

    def getRank(self, username):
        debug("getRank() username=%s" % username)
        debug(self.user_data)
        if not username in self.user_data:
            self.user_data[username] = {
                'rank' : 0,
                'questions' : 0,
                'answers' : 0,
                'level' : 0
                }
            debug(self.user_data)
        return self.user_data[username]['rank']

    def reply_text(self, session, text):
        """ Generic interface to answer """
        try:
            self.bot.reply_to(session, text)
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

    def get_commands(self, session):
        debug("get_commands()")
        if session.chat.username in self.settings["botadms"]:
            debug("User authenticated as %s." % session.chat.username)
            if session.text in COMMANDS:
                debug(" * session.text=%s" % session.text)
                command = COMMANDS[session.text]
                debug(" * command=%s" % command)
                eval(command)

    def is_it_safe(self, session):
        debug("is_it_safe()")
        if session.from_user.is_bot is True:
            debug(" * user is a bot: %s" % session.from_user.is_bot)
            return False
        if session.chat.type != 'private':
            debug(" * session.chat.type=%s" % session.chat.type)
            return False
        debug(" * SAFE")
        return True

    def bot_talk(self, session):
        message = session.text
        # safe guards
        if self.is_it_safe(session):
            self.reply_text(session, self.get_answer(UNSAFE))

        debug("session.chat.username=%s" % session.chat.username)
        self.getRank(session.chat.username)
        if self.get_answer(message):
            self.reply_text(session, self.get_answer(message))
        elif self.get_commands(session):
            pass
        else:
            msg = MISUNDERSTAND
            self.reply_text(session, msg)

    def initialized_shared_memory(self, shared_dictionary):
        debug(sys._getframe().f_code.co_name)
        self.user_data = None
        if os.path.exists(self.userdb):
            debug("Trying to restore persistent informartion.")
            try:
                with open(self.userdb, 'rb') as fd:
                    self.user_data = pickle.load(fd)
            except:
                debug("Doomed data information.  Removing file.")
                os.unlink(self.userdb)
        if self.user_data is None:
            debug("Persistent file was empty.")
            self.user_data = shared_dictionary
        debug("shared memory initialized")

    def dump_data(self):
        with open(self.userdb, 'wb') as fd:
            pickle.dump(self.user_data, fd)

    def shutdown(self):
        debug("Shuttingdow safely")
        self.dump_data()
        self.remove_lock()

botintf = TelegramBotInterface()
#with Manager() as mngr:
#    botintf.initialized_shared_memory(mngr.dict())
botintf.read_configuration()
botintf.main()
token = botintf.settings["token"]
bot = telebot.TeleBot(token)
botintf.bot = bot

def main():
    debug("polling for enquiries")
    try:
        bot.polling()
    except KeyboardInterrupt:
        pass
    botintf.shutdown()
    sys.exit(os.EX_OK)

### Bot callbacks below ###
@bot.message_handler(func=lambda m: True)
def talking(session):
    debug(session.text)
    botintf.bot_talk(session)


if __name__ == '__main__':
    main()
