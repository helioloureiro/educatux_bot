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
    "/unsafe" : "Para jogar inicie uma sessão privada com o bot.",
    "/version" : __version__
    }
COMMANDS = {
    "/reboot" : True
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
        debug("current_pid=%d" % current_pid)
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

    def getRank(self, user_id, status=False):
        debug("getRank() user_id=%s" % user_id)
        debug(self.user_data)
        if not user_id in self.user_data:
            self.user_data[user_id] = {
                'username' :  None,
                'rank' : 0,
                'questions' : 0,
                'answers' : 0,
                'level' : 0,
                'previous_message' : 0,
                'expected_answer' : None
                }
            debug(self.user_data)
        rank = float(self.user_data[user_id]['answers']) / float(self.user_data[user_id]['questions']) * 100
        self.user_data[user_id]['rank'] = rank
        return self.user_data[user_id]['rank']

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
                self.run_commands(session.text)
                return True
        return False

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

    def gaming(self, session):
        debug(sys._getframe().f_code.co_name)
        question = """Responda a correta
a) alguma coisa
b) alguma coisa
c) coisa correta
d) coisa errada
e) todas as coisas
"""
        markup = telebot.types.ReplyKeyboardMarkup(row_width=2,
                                                   one_time_keyboard=True)
        itembtna = telebot.types.KeyboardButton('a')
        itembtnb = telebot.types.KeyboardButton('b')
        itembtnc = telebot.types.KeyboardButton('c')
        itembtnd = telebot.types.KeyboardButton('d')
        itembtne = telebot.types.KeyboardButton('e')
        markup.add(itembtna,
                itembtnb,
                itembtnc,
                itembtnd,
                itembtne)
        debug(session)
        user_id = session.from_user.id
        username = session.from_user.username
        message_id = int(session.message_id) + 1 # setting the next
        expected_answer = 'c'
        self.getRank(user_id)
        self.setMessageID(user_id, message_id)
        self.setExpectedAnswer(user_id, expected_answer)
        self.incrementQuestions(user_id)
        self.bot.send_message(session.chat.id, question, reply_markup=markup)

    def incrementQuestions(self, user_id):
        self.user_data[user_id]['questions'] += 1

    def setMessageID(self, user_id, message_id):
        self.user_data[user_id]['message_id'] = message_id

    def setExpectedAnswer(self, user_id, expected_answer):
        self.user_data[user_id]['expected_answer'] = expected_answer

    def check_response(self, session):
        user_id = session.from_user.id
        username = session.from_user.username
        message_id = int(session.message_id)
        # stored values
        stored_message_id = self.getStoredMessageID(user_id)
        stored_response = self.getStoredResponse(user_id)
        if (stored_message_id + 1 != message_id):
            self.bot.reply_to(session, "Resposta não identificada.")
            # send reset here
            return
        if stored_response == session.text:
            self.incrementAnswers(user_id)
            rank = self.getRank(user_id)
            self.bot.reply_to(session, "Parabéns!  Resposta correta. Taxa de acertos em %2.2f%%" % rank)
        else:
            self.bot.reply_to(session, "Infelizmente você errou.  A resposta correta era: %s" % stored_response)
        # send reset here

    def incrementAnswers(self, user_id):
        self.user_data[user_id]['answers'] += 1

    def getStoredMessageID(self, user_id):
        return self.user_data[user_id]['message_id']

    def getStoredResponse(self, user_id):
        return self.user_data[user_id]['expected_answer']

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

    def displayRank(self, session):
        rank = self.getRank(session.from_user.id)
        self.bot.send_message(session.chat.id, "Seu índice de acerto é de %02.2f%%" % rank)

    def dump_data(self):
        with open(self.userdb, 'wb') as fd:
            pickle.dump(self.user_data, fd)

    def shutdown(self):
        debug("Shuttingdow safely")
        self.dump_data()
        self.remove_lock()

    def run_commands(self, command):
        debug("run_commands(): command=%s" % command)
        if command == "/reboot":
            return True

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
@bot.message_handler(commands=["reboot"])
def reboot(session):
    debug("Calling reboot()")
    if botintf.get_commands(session):
        debug("stop_polling()")
        bot.stop_polling()
        debug("bot stop")
        bot.stop_bot()
        sys.exit(os.EX_OK)

@bot.message_handler(commands=["rank"])
def rank(session):
    debug(session.text)
    botintf.displayRank(session)


@bot.message_handler(commands=["jogar"])
def talking(session):
    debug(session.text)
    botintf.gaming(session)


@bot.message_handler(func=lambda m: True)
def talking(session):
    responses = [ 'a', 'b', 'c', 'd', 'e' ]
    if session.text in responses:
        botintf.check_response(session)
        return
    debug(session.text)
    debug("Reply: %s" % session.reply_to_message)
    debug(session)
    botintf.bot_talk(session)



if __name__ == '__main__':
    main()
