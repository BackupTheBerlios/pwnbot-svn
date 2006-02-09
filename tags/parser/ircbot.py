#!/usr/bin/env python
# -*- coding: iso8859-15 -*-

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
from sys import exit
# es gibt mehrere Klassen. Die Verbindung als solche ist wohl die wichtigste und
# wird als erstes aufgerufen. Sie stellt die Verbindung her und kümmert sich um
# alles, was rein kommt. Nach der Verarbeitung der rohen Zeile wird ggf. eine
# andere Klasse aufgerufen,


class ircverbindung:
    def __init__(self,server,nickname,ident=None,realname=None):
        '''gleich verbinden, wenn die klasse erstellt wird'''
        self._lesebuffer = '' # wir brauchen einen leeren Buffer, in den geschrieben wird. Ein Buffer wird gebraucht, weil nicht alles sofort ankommt bei lag usw
        #log
        self._verbinde(server,nickname,ident,realname) # gleich am Anfang wird verbunden

    # Grundlegendes

    def _verbinde(self,server,nickname,ident=None,realname=None):
        '''stellt die Verbindung zum Server her und gibt zur Verarbeitung weiter

        erhält:
            server: string (host) oder tuple (host, port)
            nickname: string oder liste
            ident: optional string
            realname: optional string

        gibt zurück:
            nichts

        ruft auf:
            _verarbeite_reingehendes
        '''
        self.nicknames = []
        if type(nickname) != type([]): # Nicknames brauchen wir immer als Liste - falls einer davon belegt ist
            self.nicknames.append(nickname)
        else:
            self.nicknames.extend(nickname)
        self.currentnickname = self.nicknames.pop(0)
        ident = ident or self.currentnickname # ident und realname sind nicht so wichtig
        realname = realname or self.currentnickname # falls keine festgelegt sind, brauchen wir aber _irgendwelche_
        # ident und nickname werden in Zukunft auch gar nicht mehr gebraucht,
        # deswegen werden wir dafuer auch jetzt keine Attribute erstellen
        self.so = socket.socket()
        if type(server) != type(()):
            server = (server, 6667)
        self.so.connect(server)
        #log verbindung mit ident und realname
        self.so.send('USER %s * * :%s\r\n' % (ident, realname))
        self.so.send('NICK %s\r\n' % self.currentnickname)
        self._verarbeite_reingehendes() # Die Verbindung sollte hergestellt sein. Wir brauchen einen Loop der aus dem Buffer liest und verarbeitet

    def _verarbeite_reingehendes(self):
        '''liest den Buffer aus und verteilt das Reingehende auf die Funktionen

        erhält:
            nichts

        gibt zurück:
            nichts

        ruft auf:
            Die Funktion, deren Event zu on_EVENT passt (etwa on_PRIVMSG), mit dem Ergebnis von _teile_zeile
            Falls keine Funktion passt, wird on_UNBEKANNT mit dem Ergebnis von _teile_zeile aufgerufen

        '''

        while 1:
            try:
                self._lesebuffer = self.so.recv(8192)
            except socket.error:
                #log verbindung ist weg
                break
            if len(self._lesebuffer) == 0:
                #log verbindung ist weg
                break
            temp = self._lesebuffer.split('\n')
            self._lesebuffer = temp.pop() # Die letzte Zeile wird zurückgestellt, da sie eventuell noch gar nicht ganz zu ende war. Wir empfangen nicht Zeilen- sondern Byteweise.
            for zeile in temp:
                zeile = zeile.rstrip().split()
                if zeile[0] == 'PING': # das wird hardcoded, weil man sonst recht einfach vom server fliegt, wenn das nicht geht. Keinen Unfug damit machen!
                    self.so.send('PONG %s\r\n' % zeile[1])
                else:
                    try:
                        befehl = getattr(self,'on_%s' % zeile[1])
                        befehl(self._teile_zeile(zeile))
                    except AttributeError: # es gibt wohl keine on_EVENT Funktion für das gefundene EVENT, also rufen wir den (optionalen) Handler dafür auf
                        self.on_UNBEKANNT(self._teile_zeile(zeile))

    def _teile_zeile(self, zeile):
        ''' teilt reingehendes in ein Dictionary auf

        erhält:
            zeile: eine reinkommende Zeile als Liste

        gibt zurück:
            Dictionary:
                ['quelle']['host'],['ident'],['nickname']: string
                ['event']: string
                ['ziel']: string
                ['inhalt']: string
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
        else:
            temp['inhalt'] = zeile[2:]
        temp['inhalt'][0] = temp['inhalt'][0].lstrip(':')
        return temp

    def _teile_befehl(self,zeile):
        '''teilt erkannte Befehle in ein Dictionary auf. Was ein Befehl ist, wird in on_PRIVMSG behandelt.
        erhält:
            zeile: Dictionary:
                ['quelle']['host'],['ident'],['nickname']: string
                ['event']: string
                ['ziel']: string
                ['inhalt']: string

        gibt zurück:
            ['quelle']['host'],['ident'],['nick']: string
            ['ziel']: string
            ['befehl']: string
            ['argumente']: liste

        ruf auf:
            cmd_BEFEHL falls vorhanden, ansonsten: Fehlermeldung per notice

        '''
        befehl = {}
        befehl['quelle'] = zeile['quelle']
        befehl['ziel'] = zeile['ziel']
        if zeile['inhalt'][0].startswith(self.currentnickname):
            zeile['inhalt'].pop(0)
        befehl['befehl'] = zeile['inhalt'][0]
        befehl['argumente'] = zeile['inhalt'][1:]
        try:
            temp = getattr(self,'cmd_%s' % befehl['befehl'])
            #llog befehl erhalte
            temp(befehl)
        except AttributeError: # keine Funktion mit cmd_BEFEHL gefunden.
            #log
            self.notice(befehl['quelle']['nickname'],'Befehl nicht gefunden: %s' % befehl['befehl'])

    # Befehlshandler
    def cmd_join(self, befehl):
        '''betritt Channel

        erhält:
            Dictionary:
                ['argumente']: liste

        ruft auf:
            join für jeden Eintrag in der liste ['argumente']'''
        for channel in befehl['argumente']:
            self.join(channel)

    def cmd_say(self, befehl):
        '''sagt etwas in einem Channel

        erhält:
            befehl['argumente']: Liste

        gibt zurück:
            nichts

        ruft auf:
            msg mit argumente[0] als Ziel der Message und argumente[1:] als Message'''
        ziel = befehl['argumente'][0]
        nachricht = " ".join(befehl['argumente'][1:])
        self.msg(ziel,nachricht)

    def cmd_die(self,befehl):
        '''schaltet den Bot ab

        erhält:
            befehl['quelle']['ident']: string

        gibt zurück:
            nichts

        ruft auf:
            quit mit einer Standardmessage, falls das Ident-Field stellt
            ansonsten gibts ne notice zurück
        '''
        if befehl['quelle']['ident'] == 'tiax':
            #log
            self.quit('diediedie')
        else:
            self.notice(befehl['quelle']['nick'],'Du darfst den Bot nicht abschalten')
            #log

    def cmd_ping(self,befehl):
        '''antwortet mit pong

        erhält:
            befehl['ziel']: string

        gibt zurück:
            nichts

        ruft auf:
            msg "Pong" an Nick oder Channel
        '''
        if befehl['ziel'].startswith('#'):
            self.msg(befehl['ziel'],'Pong')
        else:
            self.notice(befehl['quelle']['nickname'],'Pong')

    def cmd_raw(self,befehl):
        '''lässt Rohdaten an den Server schicken, ist natürlich mit Vorsicht zu genießen.
        erhält:
            befehl[argumente] als Liste

        gibt zurück:
            nichts

        ruft auf:
            raw mit genau dem, was der user befiehlt'''
        
        self.rawsend(" ".join(befehl['argumente']))
 


    # für allen möglichen Käse
    def rawsend(self,rausgehendes):
        '''schickt Daten an den Server

        erhält:
            rausgehendes: string'''
        self.so.send('%s\r\n' % rausgehendes)

    # konkrete Befehle

    def join(self,channel,key=''):
        '''betritt Channel

        erhält:
            channel: string
            key: string (optional)

        ruft auf:
            rawsend
        '''
        #log
        self.rawsend('JOIN %s %s' % (channel, key))

    def msg(self,ziel,nachricht):
        '''schickt Nachrichten raus

        erhält:
            ziel: string
            nachricht: string

        ruft auf:
            rawsend
        '''
        #log
        self.rawsend('PRIVMSG %s :%s' % (ziel, nachricht))

    def notice(self,ziel,nachricht):
        '''schickt eine Nachricht als Notice raus

        erhält:
            ziel: string
            nachricht: string

        ruft auf:
            rawsend
        '''
        #log
        self.rawsend('NOTICE %s :%s' % (ziel,nachricht))

    def quit(self,quitmessage):
        '''macht den Bot aus

        erhält:
            quitmessage: string

        ruft auf:
            rawsend
        '''
        #log
        self.rawsend('quit :%s' % quitmessage)
        self.so.close()

    # Events

    # Numerics

    def on_433(self,zeile):
        ''' der nickname ist bereits belegt
        wir holen jetzt weitere nicks aus der anfangs erstellten Liste. Falls die leer wird, beenden wir den Bot'''
        try:
            self.currentnickname = self.nicknames.pop(0)
        except IndexError:
            #log
            exit('Nicknames sind ausgegangen')
        #log
        self.rawsend('NICK %s' % self.currentnickname)

    def on_001(self,zeile):
        '''die IRC Verbindung ist gerade hergestellt worden
        Das ist die ideale Gelegenheit, am Anfang auszufuehrende Befehle einzugeben'''
        #log
        pass

    # Textevents

    def on_PRIVMSG(self,zeile):
        '''bearbeitet eingehende Nachrichten'''
        if zeile['inhalt'][0].startswith(self.currentnickname) or zeile['ziel'] == self.currentnickname: # der bot wird entweder angesprochen oder er kriegt eine private message
            self._teile_befehl(zeile)
        # Ende DEBUG
    
    def on_NICK(self,zeile):
        '''jemand hat den nick geandert. Das koennten auch wir sein! damit der Bot die Befehle trotzdem als an ihn gerichtet erkennt, muss er davon in Kenntniss gesetzt werden'''
        if zeile['quelle']['nickname'] == self.currentnickname:
            self.currentnickname = zeile['inhalt'][0]
    
    def on_UNBEKANNT(self,zeile):
        '''verarbeitet alles, was nicht sonstwie verarbeitet werden kann'''
        pass

if __name__ == '__main__':
    GameSurge = ircverbindung(('irc.eu.gamesurge.net',6667),['pwn','own','pwn0r'])
