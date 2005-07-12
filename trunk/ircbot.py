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
import socket # für die IRC-Verbindung

# es gibt mehrere Klassen. Die Verbindung als solche ist wohl die wichtigste und
# wird als erstes aufgerufen. Sie stellt die Verbindung her und kümmert sich um
# alles, was rein kommt. Nach der Verarbeitung der rohen Zeile wird ggf. eine
# andere Klasse aufgerufen,


class ircverbindung:
    def __init__(self,server,nickname,ident=None,realname=None):
        '''gleich verbinden, wenn die klasse erstellt wird'''
        self.lesebuffer = '' # wir brauchen einen leeren Buffer, in den geschrieben wird. Ein Buffer wird gebraucht, weil nicht alles sofort ankommt bei lag usw
        self.verbinde(server,nickname,ident,realname) # gleich am Anfang wird verbunden

    def verbinde(self,server,nickname,ident=None,realname=None):
        '''stellt die Verbindung zum Server her
        erwartet:
        server als tuple serverurl,port
        nickname als string
        ident als string
        realname als string

        gibt nix zurück aber stellt erst die Verbindung zum IRC-Server her und ruft dann den Verarbeiter auf'''
        ident = ident or nickname
        realname = realname or nickname
        self.so = socket.socket()
        self.so.connect(server)
        # self.so.settimeout(5)
        self.so.send('USER %s * * :%s\r\n' % (ident, realname))
        print 'DEBUG:  >> USER %s * * :%s' % (ident, realname)
        self.so.send('NICK %s\r\n' % nickname)
        print 'DEBUG:  >> NICK %s' % nickname
        self.join('#the-dominion') # DEBBUG-REMOVEME
        self._verarbeite_reingehendes()

    def _verarbeite_reingehendes(self):
        '''liest den Buffer aus und verteilt das Reingehende auf die Funktionen
        erwartet: garnix
        gibt auch nix zurück, aber liest immer 1024 bytes ein und tut sie zum buffer dazu.
        die letzte zeile wird wieder zurück in den buffer getan und erst nächste mal verarbeitet,
        weil vielleicht nicht die ganze Zeile angekommen ist. So kann die Zeile erstmal vervollständigt werden.
        Wenn eine entsprechende Funktion besteht (on_FUNKTION), wird diese aufgerufen, sonst wird on_UNBEKANNT aufgerufen.
        als Spezialfall wird hier gleich PING behandelt, denn da sollte tunlichst sofort PONG zurück geschickt werden.'''

        while 1:
            try:
                self.lesebuffer = self.so.recv(8192)
            except socket.error, x:
                print "DEBUG: <> Verbindung geschlossen"
                break
            if len(self.lesebuffer) == 0:
                print "DEBUG:<> Verbindung geschlossen"
                break
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
        '''schickt Daten an den Server
        erwartet:
        das, was geschickt werden soll
        gibt auch nix zurück, erspart uns aber die lästige Fehlersuche, wenn die Zeichen am Zeilenende vergessen worden sind.'''
        self.so.send('%s\r\n' % rausgehendes)

    def join(self,channel,key=''):
        '''betritt Channel'''
        print 'DEBUG: >> Joine %s' % channel
        self.rawsend('JOIN %s %s' % (channel, key))

    def msg(self,ziel,nachricht):
        '''schickt Nachrichten raus'''
        print 'DEBUG: >> PRIVMSG an %s: %s' % (ziel, nachricht)
        self.rawsend('PRIVMSG %S :%s' % (ziel, nachricht))

    def quit(self,quitmessage):
        print 'DEBUG: <> Beende'
        self.rawsend('quit :%s' % quitmessage)
        self.so.close()

    def on_001(self,*args):
        '''die IRC Verbindung ist gerade hergestellt worden'''
        self.join('#the-dominion')

    def on_PRIVMSG(self,*args):
        '''bearbeitet eingehende Nachrichten'''
        print args
        if len(args[0]) >= 3 and args[0][3].lstrip(':') == 'die':
            self.quit('diediedie')

    def on_UNBEKANNT(self,*args):
        '''verarbeitet alles, was nicht sonstwie verarbeitet werden kann'''
        pass
