#!/bin/sh
DATEINAME=$1
NEUERDATEINAME=`python xwars.py $1`
scp $NEUERDATEINAME tiax@nerds-r-us.org:/var/www/tdm/reports/html
echo http://reports.victory-is-life.de/`echo $NEUERDATEINAME|cut -d'/' -f7`
