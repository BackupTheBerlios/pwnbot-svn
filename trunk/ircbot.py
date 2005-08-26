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
from sys import exit
from types import ListType
# es gibt mehrere Klassen. Die Verbindung als solche ist wohl die wichtigste und
# wird als erstes aufgerufen. Sie stellt die Verbindung her und kümmert sich um
# alles, was rein kommt. Nach der Verarbeitung der rohen Zeile wird ggf. eine
# andere Klasse aufgerufen,


class ircverbindung:
    def __init__(self,server,nickname,ident=None,realname=None):
        '''gleich verbinden, wenn die klasse erstellt wird'''
        self._lesebuffer = '' # wir brauchen einen leeren Buffer, in den geschrieben wird. Ein Buffer wird gebraucht, weil nicht alles sofort ankommt bei lag usw
        self._verbinde(server,nickname,ident,realname) # gleich am Anfang wird verbunden

    ##### Grundlegendes

    def _verbinde(self,server,nickname,ident=None,realname=None):
        '''stellt die Verbindung zum Server her
        erwartet:
        server entweder als string (url) oder tuple (url, port)
        nickname als liste von nicknames
        ident als string
        realname als string

        gibt nix zurück aber stellt erst die Verbindung zum IRC-Server her und ruft dann den Verarbeiter auf'''
        self.nicknames = []
        if type(nickname) != ListType:
            self.nicknames.append(nickname)
        else:
            self.nicknames.extend(nickname)
        self.currentnickname = self.nicknames.pop(0)
        ident = ident or self.currentnickname
        realname = realname or self.currentnickname
        self.so = socket.socket()
        try:
            self.so.connect(server)
        except TypeError:
            self.so.connect((server,6667))
        # self.so.settimeout(5)
        self.so.send('USER %s * * :%s\r\n' % (ident, realname))
        print 'DEBUG:  >> USER %s * * :%s' % (ident, realname)
        self.so.send('NICK %s\r\n' % self.currentnickname)
        print 'DEBUG:  >> NICK %s' % self.currentnickname
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
                self._lesebuffer = self.so.recv(8192)
            except socket.error:
                print "DEBUG: <> Verbindung geschlossen"
                break
            if len(self._lesebuffer) == 0:
                print "DEBUG:<> Verbindung geschlossen"
                break
            temp = self._lesebuffer.split('\n')
            self._lesebuffer = temp.pop()
            for zeile in temp:
                zeile = zeile.rstrip().split()
                print 'DEBUG: <<%s' % zeile
                if zeile[0] == 'PING': # das wird hardcoded, weil man sonst recht einfach vom server fliegt, wenn das nicht geht. Keinen Unfug damit machen!
                    print 'DEBUG: >> PONG an den Server geschickt'
                    self.so.send('PONG %s\r\n' % zeile[1])
                else:
                    try:
                        befehl = getattr(self,'on_%s' % zeile[1])
                        befehl(self._teile_zeile(zeile))
                    except AttributeError:
                        self.on_UNBEKANNT(self._teile_zeile(zeile))

    def _teile_zeile(self, zeile):
        ''' teilt reingehendes in ein Dictionary auf
        ['quelle']['host'],['ident'],['nickname']
        ['event']
        ['ziel']
        ['inhalt']
        '''
        temp = {}
        temp['quelle'] = {}
        if '@' in zeile[0]:
            temp['quelle']['nickname'] = zeile[0].split('!')[0].lstrip(':')
            temp['quelle']['ident'] = zeile[0].split('@')[0].split('!')[1]
            temp['quelle']['host'] = zeile[0].split('@')[1]
        else:
            temp['quelle']['nickname'], temp['quelle']['ident'], temp['quelle']['host'] = 'none','none','none'
        temp['event'] = zeile[1]
        temp['ziel'] = zeile[2]
        if len(zeile) >= 4:
            temp['inhalt'] = zeile[3:]
            temp['inhalt'][0] = temp['inhalt'][0].lstrip(':')
        return temp

    def _teile_befehl(self,zeile):
        '''teilt Befehle in ein Dictionary auf:
        befehl['quelle']['host'],['ident'],['nick']
        befehl['ziel']
        befehl['befehl']
        befehl['argumente']

        '''
        befehl = {}
        befehl['quelle'] = zeile['quelle']
        befehl['ziel'] = zeile['ziel']
        if zeile['inhalt'][0].startswith(self.currentnickname):
            zeile['inhalt'].reverse()
            zeile['inhalt'].pop()
            zeile['inhalt'].reverse()
        befehl['befehl'] = zeile['inhalt'][0]
        befehl['argumente'] = zeile['inhalt'][1:]
        print 'DEBUG: << Befehl von %s an %s: %s mit Argumenten %s' % (befehl['quelle'],befehl['ziel'],befehl['befehl'],befehl['argumente'])
        if not befehl['befehl'].startswith('_') or befehl['befehl'].startswith('on_'): #sicherheitscheck eventuell unnütz?
            try:
                temp = getattr(self,'cmd_%s' % befehl['befehl'])
                temp(befehl)
            except AttributeError:
                self.notice(befehl['quelle']['nickname'],'Befehl nicht gefunden: %s' % befehl['befehl'])
        else:
            self.notice(befehl['quelle']['nickname'],'Befehl nicht gefunden: %s' % befehl['befehl'])

    def rawsend(self,rausgehendes):
        '''schickt Daten an den Server
        erwartet:
        das, was geschickt werden soll
        gibt auch nix zurück, erspart uns aber die lästige Fehlersuche, wenn die Zeichen am Zeilenende vergessen worden sind.'''
        self.so.send('%s\r\n' % rausgehendes)

    ##### konkrete Befehle

    def join(self,channel,key=''):
        '''betritt Channel'''
        print 'DEBUG: >> Joine %s' % channel
        self.rawsend('JOIN %s %s' % (channel, key))

    def msg(self,ziel,nachricht):
        '''schickt Nachrichten raus'''
        print 'Nachricht an %s: %s' % (ziel, nachricht)
        self.rawsend('PRIVMSG %s :%s' % (ziel, nachricht))
    def notice(self,ziel,nachricht):
        '''schickt eine Nachricht als Notice raus'''
        self.rawsend('NOTICE %s :%s' % (ziel,nachricht))
    def quit(self,quitmessage):
        print 'DEBUG: <> Beende'
        self.rawsend('quit :%s' % quitmessage)
        self.so.close()

    ##### Events

    ## Numerics

    def on_433(self,zeile):
        ''' der nickname ist bereits belegt
        wir holen jetzt weitere nicks aus der anfangs erstellten Liste. Falls die leer wird, beenden wir den Bot'''
        try:
            self.currentnickname = self.nicknames.pop(0)
        except IndexError:
            exit('Nicknames sind ausgegangen')
        self.rawsend('NICK %s' % self.currentnickname)

    def on_001(self,zeile):
        '''die IRC Verbindung ist gerade hergestellt worden
        Das ist die ideale Gelegenheit, am Anfang auszufuehrende Befehle einzugeben'''
        self.join('#tiax')

    ## Textevents

    def on_PRIVMSG(self,zeile):
        '''bearbeitet eingehende Nachrichten'''
        if zeile['inhalt'][0].startswith(self.currentnickname) or zeile['ziel'] == self.currentnickname: # der bot wird entweder angesprochen oder er kriegt eine private message
            print 'DEBUG: Befehl aufgeschnappt'
            self._teile_befehl(zeile)
        # DEBUG
        if 'die' in zeile['inhalt']:
            self.quit('diediedie')
        elif 'ping' in zeile['inhalt']:
            self.msg(zeile['ziel'],'%s: pong' % zeile['quelle']['nickname'])
        print 'Nachricht von %s an %s: %s' % (zeile['quelle']['nickname'], zeile['ziel'], zeile['inhalt'])
        # Ende DEBUG

    def on_UNBEKANNT(self,zeile):
        '''verarbeitet alles, was nicht sonstwie verarbeitet werden kann'''
        pass
