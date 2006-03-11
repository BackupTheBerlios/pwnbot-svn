#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import befehle
logger = logging.getLogger()

# Events für den pwnbot
def unbekannt(event):
    event.Log()
    pass

def num_001(event):
    '''Verbindung hergestellt'''
    logger.debug('Verbindung erfolgreich etabliert')
    event.parent.join('#tiax')

def num_005(event):
    '''Was der server unterstützt'''

def PRIVMSG(event):
    '''eine Nachricht'''
    event.Log()
    event.Checkforcommand()
    if hasattr(event,'befehl'):
        befehl = getattr(befehle,event.befehl['befehl'],befehle.unbekannt)
        befehl(event)

def raw_443(event):
    try:
        event.parent.currentnickname = event.parent.nicknames.pop(0)
    except IndexError:
        logger.critical('Nicknames sind ausgegangen')
        sys.exit('Nicknames ausgegangen')