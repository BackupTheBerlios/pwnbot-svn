#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib import urlopen
from os import path
from gzip import GzipFile
from re import compile

# Konfiguration
# Mit was soll die URl anfangen?
urlstart = 'http://reports.xwars.gamigo.de/'
cachedir = '/home/tiax/xwars/cache/'
savedir = '/home/tiax/xwars/save/'

class kampfbericht:
    def __init__(self,url):
        if not path.isdir(cachedir):
            raise IOError('Cachedir existiert nicht')
        if not path.isdir(savedir):
            raise IOError('Savedir existiert nicht')
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

    def _get_namestring(self,wessen='Startbasis'):
        berichtliste = self.bericht.splitlines()
        for zeile in berichtliste:
            if wessen in zeile:
                return zeile.split('&nbsp;')[2].replace('von ','')

    def _get_name(self,):
        self.basis = {}
        if len(self._get_namestring(wessen).split()) == 2:
            self.basis['Startbasis'] = self._get_namestring('Startbasis').split()[1]
            self.basis['Zielbasis'] = self._get_namestring('Zielbasis').split()[1]
        else:
            self.basis['Startbasis'] = self._get_namestring('Startbasis')
            self.basis['Zielbasis'] = self._get_namestring('Zielbasis')
            
    def _get_koords(self,):
        berichtliste = self.bericht.splitlines()
        self.koords = {}
        for zeile in berichtliste:
            if 'Startbasis' in zeile:
                self.koords['Startbasis'] = zeile.split('<b>')[1].split('</b>')[0].strip()
            elif 'Zielbasis' in zeile:
                self.koords['Zielbasis'] = zeile.split('<b>')[1].split('</b>')[0].strip().split()[1]

    def _get_alli(self,):
        self.alli = {}
        if len(self._get_namestring(wessen).split()) == 2:
            self.alli['Startbasis'] =  self._get_namestring('Startbasis').split()[0]
            self.alli['Zielbasis'] = self._get_namestring('Zielbasis').split()[0]

    def _get_werte(self):
        berichtliste = self.bericht.splitlines()
        #flottensplit = lambda x: for item in x.strip().split(o'/')): 
        flottensplit = lambda x: tuple([int(y) for y in x.strip().split('/')])
        checkforempty = lambda x: x or ('0/0 ')
        self.flotten = []
        for zeile in berichtliste:
            if 'debug:' in zeile:
                self.flotten.append(zeile.split('<br>')[1].replace('org: ','').replace('</td>','').lstrip().split('surv:'))
       # Angreifer haben nur eine Flotte
        self.werte = {'StartbasisVorher':flottensplit(self.flotten[0][0]),'StartbasisNachher':flottensplit(checkforempty(self.flotten[0][1]))}
        self.flotten.pop(0)
        # Verteidiger sind demnach der ganze Rest
        

    def manipulate(self):
        koordinaten = compile('[0-9]{1,2}x[0-9]{1,3}x[0-9]{1,3}')
        kb_ohne_koords = koordinaten.sub('',self.bericht)
        kb_viel_hübscher = kb_ohne_koords.replace('auf Planet','auf einem Planeten').replace('Login','The Dominion').replace('Planetare Verteidigung auf','Planetare Verteidigug')
        self.bericht = kb_viel_hübscher

    def save(self):
        berichtdatei = open(savedir + self.id,'w')
        berichtdatei.write(self.bericht)
