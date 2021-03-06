#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib import urlopen
from os import path
from gzip import GzipFile
from time import strptime, strftime
from re import compile
from sys import argv

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
        startregexp = compile(r'Startbasis <b>.*(\d{1,2}x\d{1,3}x\d{1,3})</b></br>&nbsp;von ?(\[.+\])? ?(.+)&nbsp;')
        zielregexp = compile(r'Zielbasis <b>.*(\d{1,2}x\d{1,3}x\d{1,3})</b> </br>von&nbsp; ?(\[.+\])? ?(.+)&nbsp;')
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
        self.startbasis['MPVerluste'] = (StartbasisVerluste[0] + StartbasisVerluste[1]) / 200.0
        self.zielbasis['MPVerluste'] = (ZielbasisVerluste[0] + ZielbasisVerluste[1]) / 200.0

    def _make_template(self):
        template = '''</table><table border="0" cellspacing="0" cellpadding="0" width="665px"><tr><td height="12px"></td></tr><tr>
		        <td width="282px"></td>
		        <td width="45px" height="9" bgcolor="#2A2A2A"></td>
		        <td width="12px"></td>
		        <td width="45px" xbgcolor="#2A2A2A"></td>
		        <td width="281px"></td>
		  </tr>
		  <tr>
		        <td xwidth="282" colspan="2" bgcolor="#2A2A2A" height="35px">&nbsp;<b>Statistiken</b>

				<br>&nbsp;<font color="#CCCCCC">Verluste</td>
		        <td width="12px"></td>
		        <td xwidth="326px" colspan="2" xbgcolor="#2A2A2A"><font color="#222222">TDM Warreport v1 py</td>
		  </tr>
               </table>
		    
		<table border="0" cellspacing="0" cellpadding="0" width="665px">
		<tr><td bgcolor="#2A2A2A" height="9px"></td></tr>
		<tr>

			<td width= "5px" bgcolor="#2A2A2A">&nbsp;</td>
            <td width=  "5px" ></td>
            <td><b>&nbsp;Werte vorher</td>
			<td><b>&nbsp;nachher</b></td>
			<td><b>&nbsp;Milit&auml;rpunkte vorher</b></td>
            <td><b>nachher</b></td>
			<td><b>Verlust</b></td>
         </tr>
         <tr><td bgcolor="#2A2A2A" height="3"></td></tr>
        <tr><td bgcolor="#444444" height="3"></td></tr>
        <tr><td bgcolor="#444444" height="1px"></td><td colspan="12" bgcolor="#000000"></tr>
        <tr height="18px">
			<td width="50px" bgcolor="#444444">&nbsp;Angreifer</td>
            <td width=  "5px" ></td>
		    <td bgcolor="#1A1A1A">&nbsp;%(Angreiferwertevorher)s</td>
		    <td bgcolor="#1A1A1A">%(Angreiferwertenachher)s</td>
		    <td bgcolor="#1A1A1A">%(Angreifermpvorher).2f</td>
		    <td bgcolor="#1A1A1A">%(Angreifermpnachher).2f</td>
		    <td bgcolor="#1A1A1A">%(Angreifermpverlust).2f</td>
		</tr>
		<tr><td bgcolor="#444444" height="1px"></td><td colspan="12" bgcolor="#000000"></tr>
		<tr><td bgcolor="#2A2A2A" height="9"></td></tr>
        <tr height="18px">
			<td width="50px" bgcolor="#444444">&nbsp;Verteidiger</td>
            <td width=  "5px" ></td>
		    <td bgcolor="#1A1A1A">&nbsp;%(Verteidigerwertevorher)s</td>
		    <td bgcolor="#1A1A1A">%(Verteidigerwertenachher)s</td>
		    <td bgcolor="#1A1A1A">%(Verteidigermpvorher).2f</td>
		    <td bgcolor="#1A1A1A">%(Verteidigermpnachher).2f</td>
		    <td bgcolor="#1A1A1A">%(Verteidigermpverlust).2f</td>
		</tr>
		<tr><td bgcolor="#444444" height="1px"></td><td colspan="12" bgcolor="#000000"></tr>
        <tr><td bgcolor="#2A2A2A" height="9"></td></tr>
</table>
<table border="0" cellspacing="0" cellpadding="0">
		<tr>
		    <td width="50px"  bgcolor="#2A2A2A" height="35px"><br>&nbsp;</td>
		    <td width="65px"  bgcolor="#2A2A2A" align="right"><font color="CCCCCC">&nbsp;<br>&nbsp;</td>
		    <td width="20px"  bgcolor="#2A2A2A"><font color="#888888"><br></td>
		    <td width="146px" bgcolor="#2A2A2A"><font color="#CC5500">&nbsp;&nbsp;<br>&nbsp;&nbsp;<br></td>
		    <td width="45px"  bgcolor="#2A2A2A" align="right"><b>&nbsp;&nbsp;<br>&nbsp;&nbsp;</td>
		</tr>
</table>
<table border="0" cellspacing="0" cellpadding="0" width="665px"><tr><td height="12px"></td></tr><tr>''' % {'Angreifername':self.startbasis['Name'],
        'Angreiferwertevorher':str(self.startbasis['Flotte'][0]) + '/' + str(self.startbasis['Flotte'][1]),
        'Angreiferwertenachher':str(self.startbasis['Flotte'][2]) + '/' + str(self.startbasis['Flotte'][3]),
        'Angreifermpvorher':self.startbasis['MP'],
        'Angreifermpnachher':(self.startbasis['MP'] - self.startbasis['MPVerluste']),
        'Angreifermpverlust':self.startbasis['MPVerluste'],
        'Verteidigername':self.zielbasis['Name'],
        'Verteidigerwertevorher':str(self.zielbasis['Flotte'][0]) + '/' + str(self.zielbasis['Flotte'][1]),
        'Verteidigerwertenachher':str(self.zielbasis['Flotte'][2]) + '/' + str(self.zielbasis['Flotte'][3]),
        'Verteidigermpvorher': self.zielbasis['MP'],
        'Verteidigermpnachher': (self.zielbasis['MP'] - self.zielbasis['MPVerluste']),
        'Verteidigermpverlust': self.zielbasis['MPVerluste']
        }
        self.template = template

    def _make_namestring(self):
        self.namestring = '%(Angreiferallianz)s%(Angreifername)s-%(Verteidigerallianz)s-%(Verteidigername)s-%(Zeit)s' % {'Angreiferallianz':self.startbasis['Allianz'],'Angreifername':self.startbasis['Name'],'Verteidigerallianz':self.zielbasis['Allianz'],'Verteidigername':self.zielbasis['Name'],'Zeit':strftime('%Y%m%d-%H%M',self.zeit)}
        
    def _insert_template(self):
        berichtliste = self.bericht.splitlines()
        del berichtliste[berichtliste.index('                <td bgcolor="#2A2A2A" align="right">Gesamt&nbsp;<br>(netto)&nbsp;</td>') + 2]
        berichtliste.insert(berichtliste.index('                <td bgcolor="#2A2A2A" align="right">Gesamt&nbsp;<br>(netto)&nbsp;</td>') + 1,self.template)
        self.bearbeiteterbericht = berichtliste

    def manipulate(self):
        koordinatenregexp = compile(r'\d{1,2}x\d{1,3}x\d{1,3}')
        bericht = '\n'.join(self.bearbeiteterbericht)
        bericht = koordinatenregexp.sub('',bericht)
        bericht = bericht.replace('Login','The Dominion')
        bericht = bericht.replace('auf Planet','auf einem Planeten')
        bericht = bericht.replace('<title>X-Wars - The Third Legend (Gameserver)</title>','<title>%s</title>' % self.namestring)
        bericht = bericht.replace('Schiffe von','Schiffe')
        bericht = bericht.replace('Verteidigung auf','Verteidigung')
        self.bearbeiteterbericht = bericht.splitlines()
        
    def save(self):
        self.dateiname = savedir + self.namestring.replace('[','').replace(']','-') + '.html'
        berichtdatei = open(self.dateiname,'w')
        berichtdatei.writelines(self.bearbeiteterbericht)

if __name__ == "__main__":
    kb = kampfbericht(argv[1])
    kb._get_daten()
    kb._get_werte()
    kb._get_verluste()
    kb._make_template()
    kb._insert_template()
    kb._make_namestring()
    kb.manipulate()
    kb.save()
    print kb.dateiname
