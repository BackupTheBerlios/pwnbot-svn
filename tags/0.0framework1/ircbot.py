#!/usr/bin/env python
# -*- coding: iso8859-15 -*-

### ### ### ### ### ### ### ### ### ### ### ### ###
### ircbot                                      ###
###################################################
### weils keinen ircbot gab, der mir zusagte,   ###
### habe ich einen eigenen geschrieben.         ###
### das macht ihn nicht beser als die andren,   ###
### er tut aber genau das, was ich will.        ###
### ### ### ### ### ### ### ### ### ### ### ### ###

# was an modulen gebraucht wird. 
from socket import socket # f�r die IRC-Verbindung

# es gibt mehrere Klassen. Die Verbindung als solche ist wohl die wichtigste und
# wird als erstes aufgerufen. Sie stellt die Verbindung her und k�mmert sich um
# alles, was rein kommt. Nach der Verarbeitung der rohen Zeile wird ggf. eine
# andere Klasse aufgerufen, 


class ircverbindung:
    def __init__(self,server,nickname,ident,realname):
        self.lesebuffer = '' # wir brauchen einen leeren Buffer, in den geschrieben wird. Ein Buffer wird gebraucht, weil nicht alles sofort ankommt bei lag usw
        self.verbinde(server,nickname,ident,realname) # gleich am Anfang wird verbunden
        
    def verbinde(self,server,nickname,ident,realname):
        '''erwartet: 
        server als tuple serverurl,port
        nickname als string
        ident als string
        realname als string

        gibt nix zur�ck aber stellt erst die Verbindung zum IRC-Server her und ruft dann den Verarbeiter auf'''
        
        self.so = socket() 
        self.so.connect(server)
        self.so.send('USER %s * * :%s\r\n' % (ident, realname))
        print 'DEBUG:  >> USER %s * * :%s' % (ident, realname)
        self.so.send('NICK %s\r\n' % nickname)
        print 'DEBUG:  >> NICK %s' % nickname
        self.join('#tiax') # DEBBUG-REMOVEME
        self.verarbeite_reingehendes()

    def verarbeite_reingehendes(self):
        '''erwartet: garnix
        gibt auch nix zur�ck, aber liest immer 1024 bytes ein und tut sie zum buffer dazu.
        die letzte zeile wird wieder zur�ck in den buffer getan und erst n�chste mal verarbeitet,
        weil vielleicht nicht die ganze Zeile angekommen ist. So kann die Zeile erstmal vervollst�ndigt werden.

        Wenn eine entsprechende Funktion besteht (on_FUNKTION), wird diese aufgerufen, sonst wird on_UNBEKANNT aufgerufen.
        als Spezialfall wird hier gleich PING behandelt, denn da sollte tunlichst sofort PONG zur�ck geschickt werden.'''
        
        while 1:
            self.lesebuffer = self.so.recv(1024)
            temp = self.lesebuffer.split('\n')
            self.lesebuffer = temp.pop()

            for zeile in temp:
                zeile = zeile.rstrip().split()
                print 'DEBUG: <<%s' % zeile
                if zeile[0] == 'PING':
                    print 'DEBUG: >> PONG an den Server geschickt'
                    self.so.send('PONG %s\r\n' % zeile[1])
                else:
                    try:
                        befehl = getattr(self,'on_%s' % zeile[1])
                        print 'DEBUG: %s wird aufgerufen' % befehl
                        befehl(zeile)
                    except AttributeError:
                        self.on_UNBEKANNT(zeile)

    def rawsend(self,rausgehendes):
        '''erwartet:
        das, was geschickt werden soll
        gibt auch nix zur�ck, erspart uns aber die l�stige Fehlersuche, wenn die Zeichen am Zeilenende vergessen worden sind.'''
        self.so.send('%s\r\n' % rausgehendes)

    def join(self,channel,key=''):
        print 'DEBUG: >> Joine %s' % channel
        self.rawsend('JOIN %s %s' % (channel, key))
        
    def msg(self,ziel,nachricht):
        print 'DEBUG: >> PRIVMSG an %s: %s' % (ziel, nachricht)
        self.rawsend('PRIVMSG %S :%s' % (ziel, nachricht))
        
    def on_001(self,*args):
        self.join('#tiax')

    def on_PRIVMSG(self,*args):
        if args()[3].lstrip(':') == 'die':
            self.rawsend('quit')
    
    def on_UNBEKANNT(self,*args):
        pass
