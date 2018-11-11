#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Rac1.py: listen to Rac1 catalan radio station from its public podcasts'''

#    Copyright (C) 2017  Emilio del Giorgio
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Python Dependencies:
#  - requests
#  - configargparse
#  - parsedatetime
#  - datetime
#  - unicodedata
#  - sys
#  - subprocess
#  - re
#  - json
#  - psutil
#  - time
#  - signal
#  - os
#
# Other dependencies:
#  - mplayer (shell command)
#

from __future__ import print_function
import subprocess
import sys
import signal
import re
import json
import unicodedata
import requests
import configargparse


'''
    File name: Rac1.py
    Author: Emilio del Giorgio
    Date created: 2017/4/7
    Date last modified: 2018/10/20
    Python Version: 3 / 2.7
'''

__author__ = "Emilio del Giorgio"
__license__ = "GPL"
__version__ = "1.0.5"
__maintainer__ = __author__
__email__ = "github.com/emibcn"
__status__ = "Production"


def isint(value):
    '''Detect if a string has an integer value and returns the result as boolean'''

    try:
        int(value)
        return True
    except ValueError:
        return False


def normalize_encoding_upper(string):
    '''Normalizes a unicode string to an upper non-accented one'''

    try:

        # Py 2
        string = unicodedata.normalize('NFKD', string) \
            .encode('ascii', 'ignore') \
            .upper()

    except AttributeError:

        # Py 3
        string = unicodedata.normalize('NFKD', string).upper()

    return string


def parse_args(argv):
    '''Parse ARGv, `env` and config files, and return arg object'''

    class MyCustomFormatter(
            configargparse.ArgumentDefaultsHelpFormatter,
            configargparse.RawDescriptionHelpFormatter):
        '''Permet mostrar l'epilog amb la llista ben formatada, mentre es
        mostren els arguments i els seus defaults formatats correctament
        https://stackoverflow.com/questions/18462610/argumentparser-epilog-and-description-formatting-in-conjunction-with-argumentdef
        '''
        pass

    parser = configargparse.ArgParser(
        description="Escolta els podcasts de Rac1 sequencialment i sense interrupcions.",
        formatter_class=MyCustomFormatter,
        default_config_files=['/etc/Rac1/*.conf', '~/.Rac1', '~/.Rac1.*'],
        epilog="Nota: Mentre estàs escoltant un podcast amb el `mplayer`:\n"
               "- Pots passar al següent podcast prement les tecles [ENTER] o [q].\n"
               "- Pots sortir del tot prement CTRL+C\n"
               "- Pots tirar endavant i endarrere amb les tecles:\n"
               "   - SHIFT amb tecles de direccions esquerra/dreta (5s)\n"
               "   - De direccions esquerra/dreta (10s)\n"
               "   - De direccions amunt/avall (1m)\n"
               "   - De Pàgina amunt/avall (10m)\n"
    )

    parser.add_argument('-c', '--config',
                        required=False,
                        is_config_file=True,
                        help='Camí al fitxer de configuració')
    parser.add_argument('-w', '--write',
                        required=False,
                        is_write_out_config_file_arg=True,
                        help='Desa els arguments al fitxer de configuració WRITE')
    parser.add_argument("-p", "--print",
                        dest='only_print',
                        default=False,
                        action="store_true",
                        help="Només mostra el que s'executaria.")
    parser.add_argument("-u", "--print-url",
                        dest='only_print_url',
                        default=False,
                        action="store_true",
                        help="Només mostra les URLs dels podcast que s'escoltarien.")
    parser.add_argument("-d", "--date",
                        dest='date',
                        metavar="DATE",
                        default="today",
                        action="store",
                        help="El dia del que es vol escoltar els podcasts.")
    parser.add_argument("-f", "--from",
                        dest='from_hour',
                        metavar="FROM",
                        default=8,
                        type=int,
                        action="store",
                        help="La hora a partir de la que es vol escoltar la ràdio.")
    parser.add_argument("-t", "--to",
                        dest='to_hour',
                        metavar="TO",
                        default=14,
                        type=int,
                        action="store",
                        help="La hora fins la que es vol escoltar la ràdio.")
    parser.add_argument("-s", "--start-first",
                        dest='start_first',
                        metavar="START",
                        default="0",
                        action="store",
                        help=("El moment en que cal començar el primer podcast, "
                              "amb el format de l'opció '-ss' del mplayer."))
    parser.add_argument("-x", "--exclude",
                        dest='exclude',
                        metavar="EXCLUDE1[,EXCLUDE2...]",
                        default=[],
                        action="append",
                        help=("Programes a excloure, per hora o nom, "
                              "separats per coma i/o en diverses aparicions de '-x'."))
    parser.add_argument("-l", "--clean-exclude",
                        dest='exclude',
                        action='store_const',
                        const=[],
                        help=("Neteja la llista d'exclusions definida fins el moment. "
                              "No afecta posteriors entrades de '-x'."))

    # Parse arguments
    args = parser.parse_args(argv)

    # Normalize Date
    setattr(args, 'date', parse_date(args.date))

    # Normalize excludes: uppercase with no accents, splitted by comma into one-dimensional array
    excludes = []
    if len(args.exclude) > 0:

        for exc in args.exclude:

            # Exclude by hour
            if isint(exc):
                excludes.append(exc)

            # Exclude by name
            else:

                # We're treating file input data here
                # We must take care of it's encoding here
                try:
                    unicode(b'')
                except NameError: # Py3: nothing to do
                    excludes.extend(normalize_encoding_upper(exc).split(b','))
                else: # Py2: Get Unicode string decoding from UTF8
                    excludes.extend(normalize_encoding_upper(exc.decode('utf-8')).split(u','))

    # Add excludes to parsed arguments object
    setattr(args, 'excludes', excludes)

    # Return arguments and excludes
    return args


def parse_date(date_arg):
    '''Parse date and return a DD/MM/YYYY string'''

    # Can parse human-like dates, like 'date' command
    import parsedatetime as pdt
    from datetime import datetime

    # Get cal and now instances
    cal = pdt.Calendar()
    now = datetime.now()

    # Get date:
    # - From string 'date_arg'
    # - Using parsedatetime (pdt) calendar 'cal'
    # - Relative to now
    date = cal.parseDT(date_arg, now)[0]

    # Return date string parsed as DD/MM/YYYY
    return date.strftime('%d/%m/%Y')


class ExceptionDownloading(Exception):
    '''Error trying to download a page'''

    def __init__(self, message):
        self.message = message
        super(ExceptionDownloading, self).__init__(message)

    def __str__(self):
        return self.message


class ExceptionMPlayer(Exception):
    '''Error executing MPlayer'''

    def __init__(self, message):
        self.message = message
        super(ExceptionMPlayer, self).__init__(message)

    def __str__(self):
        return self.message


class Rac1(object):
    '''Class to interact to Rac1 podcasts backend API'''

    # Player PID
    _mplayer_process = None
    _process_already_exiting = False

    # Podcast cached data by audio UUID
    _podcast_data = {}

    # Arguments to customize behaviour
    args = configargparse.Namespace(
        date='today',
        from_hour='8',
        to_hour='14',
        excludes=[],
        start_first=0,
        only_print=False,
        only_print_url=False,
    )


    def __init__(self, args=args):
        self.args = args


    @classmethod
    def get_page(cls, host, path, https=False):
        '''Downloads a page'''

        headers = {
            'User-Agent': "https://github.com/emibcn/Rac1.py",
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
        }

        # Connect to server, send request and get response (and follow 3XX)
        req = requests.get(
            'http{secure}://{host}{path}'.format(
                secure=('s' if https else ''),
                host=host,
                path=path),
            headers=headers)

        return req.status_code, req.text


    def get_rac1_list_page(self, page=0):
        '''Download HTML with audio UUIDs'''

        # {date} must be in format DD/MM/YYYY
        host = "www.rac1.cat"
        path = ("/a-la-carta/cerca?"
                "text=&"
                "programId=&"
                "sectionId=HOUR&"
                "from={date}&"
                "to={date}&"
                "pageNumber={page}&"
                "btn-search=").format(
                    date=self.args.date,
                    page=page
                )

        print(u"### Descarreguem Feed HTML del llistat de Podcasts amb data {date}: {host}{path}" \
              .format(
                  date=self.args.date,
                  host=host,
                  path=path))

        status, data = self.get_page(host, path, https=True)

        if status != 200:
            raise ExceptionDownloading(
                (u"Error intentant descarregar la pàgina HTML "
                 "amb el llistat de podcasts: "
                 "{status}: {data}").format(
                     status=status,
                     data=data
                 ))

        # Return downloaded page
        return data


    @classmethod
    def parse_rac1_list_page(cls, data, discard_pages=False):
        '''Parse Rac1 data and return podcasts list in hour ascending order'''

        my_re = re.compile(r'^.* (data-[^=]*)="([^"]*)".*$')

        # Parse response:
        # - Filter lines containing data-audio-id or data-audioteca-search-page
        # - Decode from binary utf-8 to string
        # - Only get values for data-* HTML attributes, without quotes
        data_list = [re.sub(my_re, r'\1=\2', line) \
                 for line in data.split(u'\n')
                     if u'data-audio-id' in line \
                         or (not discard_pages and u'data-audioteca-search-page' in line)]

        # Filter results by type
        audio_uuid_list = [line for line in data_list if u'data-audio-id' in line]
        pages_list = [] if discard_pages else [line for line in data_list if u'data-audioteca-search-page' in line]

        # Deduply
        audio_uuid_list_dedups = []
        for uuid in audio_uuid_list:
            if uuid not in audio_uuid_list_dedups:
                audio_uuid_list_dedups.append(uuid)

        # Return segregated lists
        return audio_uuid_list_dedups, pages_list


    def get_audio_uuids(self):
        '''Get full day audio UUIDs list'''

        # Download date's first page
        data = self.get_rac1_list_page()

        # Parse downloaded data, getting UUIDs initial list and pages list
        audio_uuid_list, pages_list = self.parse_rac1_list_page(data)

        # Get extra pages, if needed
        # [1:] : remove first page, as it has already been downloaded
        for page in pages_list[1:]:

            # Get page number (discard variable name)
            _, page_number = page.split(u'=')

            # Download page uuids
            data = self.get_rac1_list_page(page_number)

            # Parse page data (discard pages list, as we already have it)
            audio_uuid_list_page, _ = self.parse_rac1_list_page(data, discard_pages=True)

            # Add audio UUIDs to the list if not already in the list
            for uuid in audio_uuid_list_page:
                if uuid not in audio_uuid_list:
                    audio_uuid_list.append(uuid)

        # Return only each audio's UUID (discard variable name)
        return [varval.split(u'=')[1] for varval in audio_uuid_list]


    def get_podcast_data(self, uuid):
        '''Download podcast information by its UUID'''

        # Return cache if already downloaded
        if uuid in self._podcast_data:
            print("#### Cached UUID: %s" % (uuid))
            return self._podcast_data[uuid]

        print("#### Download UUID: %s" % (uuid))

        host = "api.audioteca.rac1.cat"
        path = "/piece/audio?id={uuid}".format(uuid=uuid)

        # Download podcast JSON data
        status, data_raw = self.get_page(host, path, https=True)

        if status != 200:
            raise ExceptionDownloading(
                u"Error intentant descarregar el JSON amb les dades del podcast: {status}: {data}" \
                  .format(
                      status=status,
                      data=data_raw
                  ))

        # Parse JSON data
        data = json.loads(data_raw)

        # Parse the hour
        data['audio']['hour'] = int(data['audio']['time'].split(u':')[0])

        # Save cache and return parsed data
        self._podcast_data[uuid] = data
        return data


    def get_podcasts_list(self):
        '''
        Get list of podcasts from predefined URL

        - Using human readable dates (already normalized in parse_my_args)
        - From HTTP connection
        - Parse HTTP and JSON
        '''

        # Get all day audio UUIDs
        podcasts_list = [self.get_podcast_data(uuid) for uuid in self.get_audio_uuids()]

        # Return the list in reverse order
        return podcasts_list[::-1]


    def filter_podcasts_list(self, podcasts):
        '''Filters podcasts using args'''

        podcasts_filtered = []

        # Create date formatted as in downloaded podcast metainfo
        date = u'-'.join(self.args.date.split(u'/')[::-1])

        for podcast in podcasts:

            play = True

            # Only this' date podcasts (sometimes it gets other's, despite filter)
            if date != podcast['audio']['date']:
                play = False

            # From and To hours
            if not self.args.from_hour <= podcast['audio']['hour'] <= self.args.to_hour:
                play = False

            # Exclusions
            else:
                for exc in self.args.excludes:

                    # Exclude by hour and by name
                    if (isint(exc) and int(exc) == podcast['audio']['hour']) or \
                         exc in normalize_encoding_upper(podcast['audio']['title']):
                        play = False

            # If we have to play this podcast
            if play:

                # If its the first, apply the initial FastForward
                if len(podcasts_filtered) == 0:
                    podcast['start'] = self.args.start_first
                else:
                    podcast['start'] = 0

                podcasts_filtered.append(podcast)

        # Return filtred list
        return podcasts_filtered


    @classmethod
    def play_podcast_mplayer_call_args(cls, podcast):
        '''Creates the calling array for playing a podcast with MPlayer. Allows easy overriding.'''

        # Cache:
        #  - Try to play as soon as possible (with `-cache-min`)
        #  - Try to download full podcast from the beginning, aka full cache (with `-cache`)
        return [
            "mplayer",
            "-cache-min", "1",
            "-cache", str(podcast['durationSeconds'] * 10),
            "-ss", str(podcast['start']),
            podcast['path']
        ]


    def play_podcast(self, podcast):
        '''Play a podcast with mplayer, or only print the command'''

        call_args = self.play_podcast_mplayer_call_args(podcast)

        # Print URL?
        if self.args.only_print_url:
            print(podcast['path'])
            return

        # Print command?
        elif self.args.only_print:

            # Add quotes to link argument
            print_args = call_args[:]
            print_args[-1] = '"{}"'.format(podcast['path'])

            # Print execution line
            print(*print_args, sep=" ")
            return

        print(u'### Escoltem "{title}" {hour}h: {path}' \
              .format(
                  title=podcast['audio']['title'],
                  hour=podcast['audio']['hour'],
                  path=podcast['path']
              ))

        # Posem el títol a l'intèrpret de comandes
        print(u"\x1B]2;{} {}h\x07".format(podcast['audio']['title'], podcast['audio']['hour']))

        # Listen with mplayer
        # Use try to catch CTRL+C correctly
        try:
            self._mplayer_process = subprocess.call(call_args)
        except subprocess.CalledProcessError as exc:
            raise ExceptionMPlayer(u"ERROR amb MPlayer: {error}".format(error=exc.output))


    def play_podcasts_list(self, podcasts):
        '''Play all podcasts from desired list using args. Returns number of podcasts played.'''

        # Iterate, filter and play podcasts list
        done = 0
        for podcast in podcasts:
            self.play_podcast(podcast)

            done += 1

        # Return podcasts done
        return done


    def signal_handler(self, sign, *_): # Unused frame argument
        '''Exits cleanly'''

        # Don't begin exit process more than once
        if self._process_already_exiting:
            return

        self._process_already_exiting = True

        # Flush stdout and wait until mplayer exits completely
        sys.stdout.flush()
        print(u'CTRL-C!! Sortim! ({signal})'.format(signal=sign))

        # Wait a second...
        import time
        time.sleep(1)

        # If mplayer process is defined
        if self._mplayer_process is not None:
            print(u"Waiting for mplayer to finish...")

            import psutil

            try:
                # Get process info
                process = psutil.Process(self._mplayer_process)

                print(u"Killing MPlayer and all possible childs.")

                # Kill mplayer childs and wait for them to exit completely
                for proc in process.children(recursive=True):
                    proc.send_signal(signal.SIGTERM)
                    proc.wait()

                # Kill mplayer and wait for it to exit completely
                process.send_signal(signal.SIGTERM)
                process.wait()

            except psutil.NoSuchProcess:
                print(u"MPlayer already ended.")

        # Reset terminal
        #subprocess.Popen(['reset']).wait()

        # If we are handling signal, we can exit program
        exit(3)

def main(argv=None, rac1_class=Rac1):
    '''Parses arguments, gets podcasts list and play its items according to arguments'''

    # Parse ARGv
    args = parse_args(argv)

    # Instantiate main class
    rac1 = rac1_class(args=args)

    # Borrow SIGINT to exit cleanly and disable stdout buffering
    signal.signal(signal.SIGINT, rac1.signal_handler)

    # Play until none podcast is played
    # This will ensure re-download of feed when we begin to play
    # before last podcast is listed there
    done_last = 0

    while True:
        # Get list of podcasts:
        #  - Using human readable dates (already parsed at parse_my_args)
        #  - From HTTP connection (done via get_podcasts_list)
        #  - Parse XML (done via get_podcasts_list)
        try:
            podcasts = rac1.filter_podcasts_list(
                rac1.get_podcasts_list()
            )[done_last:]

        # Exit with error return value 1 on error downloading
        except ExceptionDownloading as exc:
            print(exc)
            return 1

        # If there is anything to play, do it
        if len(podcasts) > 0:
            try:
                done_last += rac1.play_podcasts_list(podcasts)

            # Exit with error return value 2 on error playing
            except ExceptionMPlayer as exc:
                print(exc)
                return 2

        # If we couldn't play anything, don't try to download
        # the list again: there will be nothing, again
        else:
            break

        # If we are only printing URLs (again, we played nothing), stop trying, too
        if args.only_print or args.only_print_url:
            break

    return 0

if __name__ == "__main__":
    exit(main())
