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
import socket # für die IRC-Verbindung
import sys
import time
import os
import xwars

class ircevent(object):
    '''Etwas im IRC ist passiert'''
    __slots__ = ['quelle','ziel','event','inhalt','parent']
    quelle = {}

    def __init__(self,zeile,parent):
        self.parent = parent
        self._teile(zeile)
        print self

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
        self.ziel = zeile.pop(0)
        zeile[0] = zeile[0].lstrip(':')
        self.inhalt = zeile

    def Log(self):
        '''schreibt das event ins logfile'''
        pass

    def Checkforcommand(self):
        '''Überprüft die den Inhalt auf einen Befehl und gibt den zurück bei Erfolg, ansonsten nichts'''
        if self.inhalt[0].startswith(self.parent.nick) or self.ziel == self.parent.nick:
            if self.inhalt[0].startswith(self.parent.nick): self.inhalt.pop(0)
            befehl = self.inhalt.pop(0)
            argumente = self.inhalt
            return {'befehl':befehl,'argumente':argumente}
        else:
            return False