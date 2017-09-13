# Rac1.py
Little script to listen to Rac1 catalan radio station from its public podcasts

## Script help (catalan)

```
Usage: Rac1.py [-h] [-p] [-d DATE] [-f FROM] [-t TO] [-s START]
               [-x EXCLUDE1[,EXCLUDE2...]] [-c]

Escolta els podcasts de Rac1 sequencialment i sense interrupcions

optional arguments:
  -h, --help            show this help message and exit
  -p, --print           Només mostra el que s'executaria. (default: False)
  -d DATE, --date DATE  El dia del que es vol escoltar els podcasts. (default:
                        today)
  -f FROM, --from FROM  La hora a partir de la que es vol escoltar la ràdio.
                        (default: 8)
  -t TO, --to TO        La hora fins la que es vol escoltar la ràdio.
                        (default: 14)
  -s START, --start-first START
                        El moment en que cal començar el primer podcast, amb
                        el format de l'opció '-ss' del mplayer. (default: 0)
  -x EXCLUDE1[,EXCLUDE2...], --exclude EXCLUDE1[,EXCLUDE2...]
                        Programes a excloure, per hora o nom, separats per
                        coma i/o en diverses aparicions de '-x'. (default:
                        ['SEGONA HORA,PRIMER TOC'])
  -c, --clean-exclude   Neteja la llista d'exclusions definida fins el moment.
                        No afecta posteriors entrades de '-x'. (default: None)

Nota: Mentre estàs escoltant un podcast, pots passar al següent
prement les tecles [ENTER] o [q].

Pots sortir del tot prement CTRL+C

Pots tirar endavant i endarrere amb les tecles:
   - De direccions esquerra/dreta (10s)
   - De direccions amunt/avall (1m)
   - De Pàgina amunt/avall (10m)
```
