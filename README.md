# Rac1.py
Small script to listen to Rac1 catalan radio station from its public podcasts.

## Compatibility
Python 2 & 3

## Install
Just need to install this package using `pip` or `pip3`. You can install it inside or not of a virtualenv. Also, it uses **mplayer** to play podcasts, so consider installing it using your distro repo manager. For example, for Debian/Ubuntu:

```sh
sudo apt install mplayer
```

### Using pip
```sh
pip install -U https://github.com/emibcn/Rac1.py.git
```

### Using a virtualenv
```sh
source bin/activate
pip install -U https://github.com/emibcn/Rac1.py.git
```

## Known issues & TODO
Rac1 has recently changed its podcasts infrastructure. Now we need to
download plain HTML to get a paginated list of the audios published on a
date. It's not optimal (it would be better to call an API URL to get this
as a JSON list), but it's functional.

## See also
[Joan Domingo's - Podcasts-RAC1-Android](https://github.com/joan-domingo/Podcasts-RAC1-Android)

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

## Examples
```
# Listen to the podcasts published today
Rac1.py -d today
# Listen to the podcasts published yesterday
Rac1.py -d yesterday
# Listen to the podcasts published last friday
Rac1.py -d 'last friday'
# List the podcasts URLs published last friday
Rac1.py -d 'last friday' -p
# List the podcasts URLs published last friday beginning at 8:30am
Rac1.py -d 'last friday' -p -s 30:00
```
