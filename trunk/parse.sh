#!/bin/sh
DATEINAME=$1
NEUERDATEINAME=`python xwars.py $1`
scp $NEUERDATEINAME tiax@nerds-r-us.org:/var/www/tiax/eee
echo http://eee.planet-tiax.de/`echo $NEUERDATEINAME|cut -d'/' -f7`
