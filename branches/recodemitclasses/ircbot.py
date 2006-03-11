#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ## ### ### ### ### ### ### ### ### ### ### ###
# ircbot
# $Author$
# $Date$
# $Rev$
# ###############################################
# # weils keinen ircbot gab, der mir zusagte,   #
# # habe ich einen eigenen geschrieben.         #
# # das macht ihn nicht beser als die andren,   #
# # er tut aber genau das, was ich will.        #
# # ### ### ### ### ### ### ### ### ### ### ### #

# was an modulen gebraucht wird.
import socket
import sys
import time
import os
import xwars
import logging
import events
from logging.handlers import RotatingFileHandler

logger = None

def logstart(size):
    global logger
    logger = logging.getLogger()
    handler = RotatingFileHandler('ircbot.log','a',size * 1024, 5)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

class IRCError(Exception):
    pass

class ircevent(object):
    '''Etwas im IRC ist passiert'''
    __slots__ = ['quelle','ziel','event','inhalt','parent','befehl']
    quelle = {}

    def __init__(self,zeile,parent):
        self.parent = parent
        self._teile(zeile)

    def __repr__(self):
        return "\n".join(("Quelle:" + str(self.quelle), "Ziel: " + self.ziel, "Event: " + self.event, " ".join(self.inhalt)))

    def _teile(self,zeile):
        '''teilt die Zeile in Attribute für die Klase auf'''
        zeile = zeile.split()
        quelle = zeile.pop(0).split('!')
        self.quelle['nick'] = quelle[0].lstrip(':')
        try:
            self.quelle['ident'] = quelle[1]
        except IndexError:
            self.quelle['ident'], self.quelle['host'] = (None, None)
        else:
            self.quelle['ident'] = quelle[1].split('@')[0]
            self.quelle['host'] = quelle[1].split('@')[1]
        self.event = zeile.pop(0)
        if self.event.isdigit():
            self.event = "num_%s" % self.event
        self.ziel = zeile.pop(0)
        if len(zeile) > 0:
            zeile[0] = zeile[0].lstrip(':')
        self.inhalt = zeile

    def Log(self):
        '''schreibt das event ins logfile'''
        if self.ziel == self.parent.currentnickname:
            logkategorie = self.quelle['nick']
        else:
            logkategorie = self.ziel
        INlogger = logging.getLogger('IN-%s' % logkategorie)
        INlogger.debug('%s %s %s' % (str(self.quelle),self.event," ".join(self.inhalt)))


    def Checkforcommand(self):
        '''Überprüft die den Inhalt auf einen Befehl und gibt den zurück bei Erfolg, ansonsten nichts'''
        if self.inhalt[0].startswith(self.parent.currentnickname) or self.ziel == self.parent.currentnickname:
            if self.inhalt[0].startswith(self.parent.currentnickname): self.inhalt.pop(0)
            befehl = self.inhalt.pop(0)
            argumente = self.inhalt
            self.befehl = {'befehl':befehl,'argumente':argumente}

class ircverbindung(object):
    def __init__(self,server,nickname,ident=None,realname=None):
        global logger
        self._buffer = ''
        logger.debug('Verbindung zu %s wird hergestellt' % server)
        self.Verbinde(server,nickname,ident,realname)

    def Verbinde(self,server,nickname,ident=None,realname=None):
        self.nicknames = []
        if type(nickname) == type([]):
            self.nicknames.extend(nickname)
        else:
            self.nicknames.append(nickname)
        self.currentnickname = self.nicknames.pop(0)
        ident = ident or self.currentnickname
        realname = realname or self.currentnickname
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._socket.connect(server)
        except TypeError:
            self._socket.connect((server,6667))
        logger.info('Verbindung zu %s wurde hergestellt' % server)
        self.rawsend('USER %s * * :%s' % (ident, realname))
        self.rawsend('NICK %s' % self.currentnickname)
        self._verarbeite()

    def _verarbeite(self):
        while True:
            try:
                self._buffer = self._socket.recv(8192)
            except socket.error:
                logger.critical('Verbindung unterbrochen')
                break
            if len(self._buffer) == 0:
                logger.critical('Verbindung unterbrochen')
                break
            temp = self._buffer.split('\n')
            self._buffer = temp.pop()
            for zeile in temp:
                zeile = zeile.rstrip()
                if zeile.split()[0] == 'PING':
                    self.rawsend('PONG %s' % zeile.split()[1])
                else:
                    event = ircevent(zeile,self)
                    handler = getattr(events,event.event,events.unbekannt)
                    handler(event)

    def rawsend(self, zeile):
        self._socket.send('%s\r\n' % zeile)

    def join(self,channel,key=''):
        logger.debug('Betrete %s' % channel)
        self.rawsend('JOIN %s %s' % (channel,key))

    def part(self,channel):
        logger.debug('Verlasse %s' % channel)
        self.rawsend('PART %s' % channel)

    def quit(self,quitmessage='weq'):
        logger.info('Beende die Verbindung')
        self.rawsend('QUIT :%s' % quitmessage)

    def msg(self,ziel,message):
        logger.debug('Message an %s: %s' % (ziel, message))
        self.rawsend('PRIVMSG %s :%s' % (ziel, message))

    def notice(self,ziel,message):
        logger.debug('Notice an %s: %s' % (ziel, message))
        self.rawsend('NOTICE %s :%s' % (ziel, message))

logstart(1024)