#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xwars
import logging

logger = logging.getLogger('plugins')

def _checkfortiax(event):
    return event.quelle['ident'] == 'tiax' and event.quelle['host'] == 'victory-is-life.de'
def quit(event):
    if _checkfortiax(event):
        event.parent.quit('Shutdown: %s' % ' '.join(event.befehl['argumente']))
    else:
        event.parent.notice(event.quelle['nick'],'Nicht berechtigt')

def ping(event):
    event.parent.notice(event.quelle['nick'],'Pong')

def join(event):
    if _checkfortiax(event):
        event.parent.join(' '.join(event.befehl['argumente']))

def part(event):
    if _checkfortiax(event):
        event.parent.part(' '.joing(event.befehl['argumente']))

def say(event):
    if _checkfortiax(event):
        event.parent.msg(event.befehl['argumente'].pop(0),' '.join(event.befehl['argumente']))

def parse(event):
    print event.ziel
    if event.ziel == '#tdm':
        try:
            url = event.befehl['argumente'][0]
        except IndexError:
            event.parent.notice(event.quelle['nick'],'Bitte URL angeben')
        else:
            logger.info('%s lässt %s parsen' % (event.quelle, url))
            kampfbericht = xwars.kampfbericht(url)
            try:
                kampfbericht.analyze()
            except (IOError), meldung:
                self.notice(event.quelle['nick'],meldung)
            except AttributeError:
                self.notice(event.quelle['nick'],'Ungültige URL')
            else:
                kampfbericht.manipulate()
                kampfbericht.save()
                event.parent.notice(event.quelle['nick'],'URL: ' + kampfbericht.dateiname)

def unbekannt(event):
    event.parent.notice(event.quelle['nick'],'Befehl nicht gefunden')
