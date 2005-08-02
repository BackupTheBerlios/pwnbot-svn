#!/usr/bin/env python
# -*- coding: iso8859-15 -*-
'''stellt mehrere log-funktionen zur Verfügung'''

from sys import exit
from time import strftime
class EinzelDateiLogger:
    def __init__(self,dateiname):
        '''öffnet die Datei

        erwartet: dateiname des Logfiles. Das Verzeichnis in dem es liegt, muss existieren!'''
        try:
            self.logdatei = open(dateiname,'a',1)
        except IOError:
            exit('Verzeichnis nicht vorhanden')

    def log(self,kategorie,nachricht):
        '''erstellt erst ein Datum und schreibt dann in die Datei
        
        erwartet: 
        kategorie als string
        nachricht als string
        
        gibt zurück: nichts, schreibt aber im Format YYYY-MM-DD HH:MM:SS | Kategorie | Hier die Nachricht in die Datei. Dabei werden in der Nachricht alle | durch / ersetzt.'''
        datum = strftime('%Y-%m-%d %H:%M:%S')
        self.logdatei.write('%s|%s|%s\n' % (datum,kategorie,nachricht.replace('|','/')))
    
    def flush(self):
        '''sicherheitshalber noch das flush-feature weiterreichen'''
        self.logdatei.flush()
