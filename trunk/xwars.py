#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib import urlopen
from os import path
from gzip import GzipFile
from time import strptime
from re import compile

# Konfiguration
# Mit was soll die URl anfangen?
urlstart = 'http://reports.xwars.gamigo.de/'
cachedir = '/home/tiax/xwars/parser/cache/'
savedir = '/home/tiax/xwars/parser/save/'

class kampfbericht:
    def __init__(self,url):
        if not path.isdir(cachedir):
            raise IOError('Cachedir existiert nicht')
        if not path.isdir(savedir):
            raise IOError('Savedir existiert nicht')
        self.startbasis = {}
        self.zielbasis = {}
        self.url = url    
        self._get_id()
        self._get_kb()

    def _get_id(self):
        '''überprüft kampfbericht-urls auf ihre gültigkeit

        gets: url/string
        returns: kampfberichtid/string'''
        
        if not self.url.startswith(urlstart):
            raise IOError('Ungültiger Server')
        if not (self.url.split('=')[1].startswith('combat') and self.url.split('=')[1].endswith('.html')):
            raise IOError('Ugültige ID')
        else:
            self.id =  self.url.split('=')[1].rstrip('.html')

    def _get_kb(self):
        '''holt den kampfbericht hervor 
        überprüft zunächst, ob er vielleicht bereits abgerufen worden ist und lädt dann aus dem cache'''
        if path.isfile(cachedir + self.id):
            self.bericht = GzipFile(cachedir + self.id,'r').read()
        else:
            bericht = urlopen('%(urlstart)s?id=%(berichtid)s.html' % {'urlstart':urlstart,'berichtid':self.id}).read()
            cachedatei = GzipFile(cachedir + self.id,'w')
            cachedatei.write(bericht)
            cachedatei.close()
            self.bericht =  bericht

    def _get_daten(self):
        startregexp = compile(r'Startbasis <b> (.+)</b></br>&nbsp;von ?(\[.+\])? ?(.+)&nbsp;')
        zielregexp = compile(r'Zielbasis <b> (.+)</b> </br>von&nbsp; ?(\[.+\])? ?(.+)&nbsp;')
        uhrzeitregexp = compile(r'Zeit <b>(\d+.\d+.\d+) (\d+:\d+:\d+.*)</b>')
        self.startbasis['Koordinaten'],self.startbasis['Allianz'], self.startbasis['Name'] = startregexp.search(self.bericht).groups()
        self.zielbasis['Koordinaten'], self.zielbasis['Allianz'], self.zielbasis['Name'] = zielregexp.search(self.bericht).groups()
        self.zeit = strptime(" ".join(uhrzeitregexp.search(self.bericht).groups()), '%d.%m.%Y %H:%M:%S')
        
    def _get_werte(self):
        flottenregexp = compile(r'org: (\d+)/(\d+) surv: (\d+)?/(\d+)?')
        flotten = flottenregexp.findall(self.bericht)
        # Angreifer haben nur eine Flotte und sind schnell erledigt
        # self.startbasis['Flotte'] = flotten.pop(0)
        templiste = []
        for item in flotten.pop(0):
            templiste.append(int((item or 0)))
        self.startbasis['Flotte'] = tuple(templiste)
        self.startbasis['MP'] = (self.startbasis['Flotte'][0] + self.startbasis['Flotte'][1]) / 200.0
        # Verteidiger haben mehrere + Defense aber das zählen wir alles zusammen
        AttVorher, DefVorher, AttNachher, DefNachher = 0,0,0,0
        for item in flotten:
            AttVorher += int((item[0]) or 0)
            DefVorher += int((item[1]) or 0)
            AttNachher += int((item[2]) or 0)
            DefNachher += int((item[3]) or 0)
        self.zielbasis['Flotte'] = (AttVorher, DefVorher, AttNachher, DefNachher)
        self.zielbasis['MP'] = (AttVorher + DefVorher) / 200.0
        
    def _get_verluste(self):
        StartbasisVerluste = (abs(self.startbasis['Flotte'][0] - self.startbasis['Flotte'][2]), abs(self.startbasis['Flotte'][1] - self.startbasis['Flotte'][3]))
        ZielbasisVerluste = (abs(self.zielbasis['Flotte'][0] - self.zielbasis['Flotte'][2]), abs(self.zielbasis['Flotte'][1] - self.zielbasis['Flotte'][3]))
        self.startbasis['Verluste'] = StartbasisVerluste
        self.zielbasis['Verluste'] = ZielbasisVerluste
        self.startbasis['MPVerluste'] = (StartbasisVerluste[0] + StartbasisVerluste[1]) / 200
        self.zielbasis['MPVerluste'] = (ZielbasisVerluste[0] + ZielbasisVerluste[1]) / 200

    def save(self):
        berichtdatei = open(savedir + self.id,'w')
        berichtdatei.write(self.bericht)
