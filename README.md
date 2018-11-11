
[![Build Status](https://travis-ci.com/emibcn/Rac1.py.svg?branch=master)](https://travis-ci.com/emibcn/Rac1.py)

# Rac1.py
Small script to listen to Rac1 catalan radio station from its public podcasts.

# Index
- [Compatibility](#compatibility)
- [Install](#install)
  - [Using pip only for user](#using-pip-only-for-user)
  - [Using pip system wide](#using-pip-system-wide)
  - [Download and install for development](#download-and-install-for-development)
- [Known issues & TODO](#known-issues--todo)
  - [Arguments, environment and config files](#arguments-environment-and-config-files)
- [See also](#see-also)
- [Script help (catalan)](#script-help-catalan)
- [Examples](#examples)
  - [Using Rac1.py as a library](#using-rac1py-as-a-library)
    - [Using `vlc` instead of `mplayer`](#using-vlc-instead-of-mplayer)

## Compatibility
Python 2 & 3

## Install
Just need to install this package using `pip` or `pip3`. You can install it inside or not of a virtualenv. Also, it uses **mplayer** to play podcasts, so consider installing it using your distro repo manager. For example, for Debian/Ubuntu:

```sh
sudo apt install mplayer
```

### Using pip only for user
```sh
pip install -U --user https://github.com/emibcn/Rac1.py.git
```

### Using pip system wide
```sh
pip install -U https://github.com/emibcn/Rac1.py.git
```

### Download and install for development
```sh
# Go to HOME directory (or where ever you want to download the project)
cd

# Download project
git clone https://github.com/emibcn/Rac1.py.git

# Install with `pip` with editable mode (i.e. setuptools "develop mode")
pip install -U --user -e Rac1.py/
```

## Known issues & TODO
Rac1 has recently changed its podcasts infrastructure. Now we need to
download plain HTML to get a paginated list of the audios published on a
date. It's not optimal (it would be better to call an API URL to get this
as a JSON list), but it's functional.

### Arguments, environment and config files
I've recently switched from ArgParser (popular arguments parsing) to ConfigArgParse, which extends
ArgParser to support config file parsing and environment variables too. This library works mostly well,
but still have some inconsistencies. For example, if you define some excludes at your config file and
declare some other via arguments, you will expect all of them to be together. Instead of that, it
overwrites the config file excludes with the arguments ones (sic).

## See also
[Joan Domingo's - Podcasts-RAC1-Android](https://github.com/joan-domingo/Podcasts-RAC1-Android)

## Script help (catalan)

```
usage: Rac1.py [-h] [-c CONFIG] [-w WRITE] [-p] [-u] [-d DATE] [-f FROM]
               [-t TO] [-s START] [-x EXCLUDE1[,EXCLUDE2...]] [-l]

Escolta els podcasts de Rac1 sequencialment i sense interrupcions. Args that start with '--' (eg. -p) can also be set in a config file (/etc/Rac1/*.conf or ~/.Rac1 or ~/.Rac1.* or specified via -c). Config file syntax allows: key=value, flag=true, stuff=[a,b,c] (for details, see syntax at https://goo.gl/R74nmi). If an arg is specified in more than one place, then commandline values override config file values which override defaults.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Camí al fitxer de configuració (default: None)
  -w WRITE, --write WRITE
                        Desa els arguments al fitxer de configuració WRITE
                        (default: None)
  -p, --print           Només mostra el que s'executaria. (default: False)
  -u, --print-url       Només mostra les URLs dels podcast que s'escoltarien.
                        (default: False)
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
                        coma i/o en diverses aparicions de '-x'. (default: [])
  -l, --clean-exclude   Neteja la llista d'exclusions definida fins el moment.
                        No afecta posteriors entrades de '-x'. (default: None)

Nota: Mentre estàs escoltant un podcast amb el `mplayer`:
- Pots passar al següent podcast prement les tecles [ENTER] o [q].
- Pots sortir del tot prement CTRL+C
- Pots tirar endavant i endarrere amb les tecles:
   - SHIFT amb tecles de direccions esquerra/dreta (5s)
   - De direccions esquerra/dreta (10s)
   - De direccions amunt/avall (1m)
   - De Pàgina amunt/avall (10m)
```

## Examples
```sh
# Listen to the podcasts published today
Rac1

# Listen to the podcasts published yesterday
Rac1 -d yesterday

# Listen to the podcasts published last friday
Rac1 -d 'last friday'

# List the podcasts URLs published last friday
Rac1 -d 'last friday' -p

# List the podcasts URLs published last friday beginning at 8:30am
Rac1 -d 'last friday' -p -s 30:00

# Save to default config file the options:
# - Listen to the podcasts published yesterday
# - From 7 to 17h
# - Excluding programs whith name containing 'ESPANYOL JUGA'
Rac1 -d yesterday -f 7 -t 17 -x 'ESPANYOL JUGA' -w ~/.Rac1
```

I don't like futbol in general, so my defaults are:

```sh
Rac1 -f 8 -t 14 -x 'JUGA A RAC','TU DIRAS','PRIMER TOC' -w ~/.Rac1

```

And that creates a configuration file with the following contents:


```
from = 8
to = 14
exclude = [JUGA A RAC,TU DIRAS,PRIMER TOC]
date = today

```

### Using Rac1.py as a library
There are multiple ways you can re-use this library:

#### Using `vlc` instead of `mplayer`
If you want to use `vlc` instead of `mplayer`, you can extend `Rac1.py`:
```python
import Rac1

class VlcPlayer(Rac1.PlayerCommand):

    command_name = "VLC"

    @classmethod
    def play_podcast_command_call_args(cls, podcast):

        # Parse seconds for dumb vlc
        time_list = str(podcast['start']).split(':')
        seconds = 0
        while len(time_list):
            unit = int(time_list.pop(0))
            seconds = (60 * seconds) + unit

        return [
            "vlc",
            "--play-and-exit",
            "--file-caching", str(podcast['durationSeconds'] * 10),
            "--start-time", str(seconds),
            podcast['path']
        ]

exit(Rac1.main(player_class=VlcPlayer))
```
