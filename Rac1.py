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


class ExceptionPlayer(Exception):
    '''Error executing Player'''

    def __init__(self, message):
        self.message = message
        super(ExceptionPlayer, self).__init__(message)

    def __str__(self):
        return self.message


def get_page(host, path, https=False):
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


class Rac1(object):
    '''Class to interact to Rac1 podcasts backend API'''

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

        status, data = get_page(host, path, https=True)

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
        '''
        Parse Rac1 page data and a tuple of 2 generators:
        - Podcasts UUIDs generator in hour ascending order
        - Page numbers generator
        '''

        my_re = re.compile(r'^.* (data-[^=]*)="([^"]*)".*$')

        # Parse response:
        # - Filter lines containing data-audio-id or data-audioteca-search-page
        # - Only get values for data-* HTML attributes, without quotes
        data_list = (
            re.sub(my_re, r'\1=\2', line).split(u'=')
            for line in data.split(u'\n')
            if u'data-audio-id' in line \
                or (not discard_pages and u'data-audioteca-search-page' in line))

        # Convert to list if we need pages generator (cache), let as generator if not
        if not discard_pages:
            data_list = list(data_list)

        # Filter results by type
        audio_uuid_list = (
            line[1]
            for line in data_list
            if line[0] == u'data-audio-id')
        pages_list = () if discard_pages else (
            line[1]
            for line in data_list
            if line[0] == u'data-audioteca-search-page')

        # Return segregated lists
        return audio_uuid_list, pages_list


    def get_audio_uuids(self):
        '''Full day audio UUIDs generator'''

        # Download and parse first page data, getting UUIDs initial list and pages list
        audio_uuid_list_page, pages_list = self.parse_rac1_list_page(self.get_rac1_list_page())

        # Remember yielded UUIDs
        audio_uuid_list = []

        # Yield already downloaded uuids
        for uuid in audio_uuid_list_page:
            if uuid not in audio_uuid_list:
                audio_uuid_list.append(uuid)
                yield uuid

        # Get extra pages, if needed
        # Jump first page, as it has already been downloaded
        next(pages_list)
        for page in pages_list:

            # Download and parse page UUIDs (discard pages generator, as we already have it)
            audio_uuid_list_page, _ = self.parse_rac1_list_page(
                self.get_rac1_list_page(page),
                discard_pages=True)

            # Add to list and yield audio UUIDs if not already in list
            for uuid in audio_uuid_list_page:
                if uuid not in audio_uuid_list:
                    audio_uuid_list.append(uuid)
                    yield uuid


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
        status, data_raw = get_page(host, path, https=True)

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


    def get_podcasts(self):
        '''
        Podcasts generator from predefined URL

        - Using human readable dates (already normalized in parse_my_args)
        - From HTTP connection
        - Parse HTTP and JSON
        '''

        # Get all day audio UUIDs and return it in reverse order
        # Need to get list from generator to invert order
        for uuid, _ in list(
                (uuid, print(u"#### Got UUID: %s" % (uuid)))
                for uuid in self.get_audio_uuids()
        )[::-1]:
            yield self.get_podcast_data(uuid)


    def filter_podcasts(self, podcasts):
        '''Generator for filtered podcasts using args'''

        is_first = True

        # Create date formatted as in downloaded podcast metainfo
        date = u'-'.join(self.args.date.split(u'/')[::-1])

        # Process iterable generator and yield filtered podcasts
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

                # If its the first one, apply the initial FastForward
                podcast['start'] = self.args.start_first if is_first else 0
                is_first = False

                # Yield filtered podcast
                yield podcast

            else:
                print(u'### Filtrem "{title}" {hour}h: {path}' \
                      .format(
                          title=podcast['audio']['title'],
                          hour=podcast['audio']['hour'],
                          path=podcast['path']
                      ))

            # Stop yielding (thus, downloading UUIDs) once `to_hour` is reached
            if podcast['audio']['hour'] >= self.args.to_hour:
                break


    def get_filtered_podcasts(self):
        '''Returns filtered podcasts generator'''
        return self.filter_podcasts(
            self.get_podcasts())


    def get_autoreloaded_podcasts(self):
        '''Generator for an autoreloaded list of podcasts'''

        # Play until none podcast is played
        # This will ensure re-download of feed when we begin to play
        # before last podcast is listed there
        done_total = 0

        while True:
            # Get and play list of podcasts:
            #  - Using human readable dates (already parsed at parse_my_args)
            #  - From HTTP connection (done via get_podcasts)
            #  - Parse XML (done via get_podcasts)
            #  - Filtered by user provided options (done via filter_podcasts)
            #  - Discarding initial `done_total` podcasts
            #  - Playing with mplayer (done via play_podcast)
            #  - Handling two possible expected Exceptions to exit cleanly
            done = 0
            try:
                for i, podcast in enumerate(self.get_filtered_podcasts()):

                    # Discard already played podcasts
                    if i >= done_total:
                        done += 1

                        # Yield podcast
                        yield podcast

            except ExceptionDownloading:
                raise

            # If anything was played, sum it to total
            if done > 0:
                done_total += done

            # If we couldn't play anything, don't try to download
            # the list again: there will be nothing, again
            else:
                break

            # If we are only printing URLs (again, we played nothing), stop trying, too
            if self.args.only_print or self.args.only_print_url:
                break


class PlayerCommand(object):
    '''Class to play Rac1 podcasts with external command'''

    command_name = "Virtual Player"

    # Player PID
    _process = None
    _process_already_exiting = False

    # Arguments to customize behaviour
    args = configargparse.Namespace(
        only_print=False,
        only_print_url=False,
    )


    def __init__(self, args=args):
        self.args = args


    @classmethod
    def play_podcast_command_call_args(cls, podcast):
        '''
        Creates the calling array for playing a podcast with a command.
        Must be implemented by subclass.
        '''
        raise NotImplementedError((u"Subclass should implement command "
                                   "arguments creation as a `@classmethod`."))


    def play_podcast(self, podcast):
        '''Play a podcast with an external command, or only print the command'''

        call_args = self.play_podcast_command_call_args(podcast)

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

        # Set title for command manager
        print(u"\x1B]2;{} {}h\x07".format(podcast['audio']['title'], podcast['audio']['hour']))

        # Listen with command
        # Use try to catch CTRL+C correctly
        try:
            self._process = subprocess.call(call_args)
            self._process = None

        except subprocess.CalledProcessError as exc:
            raise ExceptionPlayer(u"ERROR amb {command}: {error}".format(
                command=self.command_name,
                error=exc.output))


    def signal_handler(self, sign, *_): # Unused frame argument
        '''Exits cleanly'''

        # Don't begin exit process more than once
        if self._process_already_exiting:
            return

        self._process_already_exiting = True

        # Flush stdout and wait until process exits completely
        sys.stdout.flush()
        print(u'CTRL-C!! Sortim! ({signal})'.format(signal=sign))

        # Wait a second...
        import time
        time.sleep(1)

        # If mplayer process is defined
        if self._process is not None:
            print(u"Waiting for {command} to finish...".format(command=self.command_name))

            import psutil

            try:
                # Get process info
                process = psutil.Process(self._process)

                print(u"Killing {command} and all possible childs.".format(
                    command=self.command_name))

                # Kill process childs and wait for them to exit completely
                for proc in process.children(recursive=True):
                    proc.send_signal(signal.SIGTERM)
                    proc.wait()

                # Kill process and wait for it to exit completely
                process.send_signal(signal.SIGTERM)
                process.wait()

            except psutil.NoSuchProcess:
                print(u"{command} already ended.".format(command=self.command_name))

        # Reset terminal
        #subprocess.Popen(['reset']).wait()

        # If we are handling signal, we can exit program
        exit(3)



class MPlayerCommand(PlayerCommand):
    '''Class to play Rac1 podcasts using MPlayer command'''

    command_name = "MPlayer"

    @classmethod
    def play_podcast_command_call_args(cls, podcast):
        '''Creates the calling array for playing a podcast with MPlayer'''

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


def main(argv=None, rac1_class=Rac1, player_class=MPlayerCommand):
    '''Parses arguments, gets podcasts list and play its items according to arguments'''

    # Parse ARGv
    args = parse_args(argv)

    # Instantiate main class
    rac1 = rac1_class(args=args)

    # Instantiate player class
    player = player_class(args=args)

    # Borrow SIGINT to exit cleanly and disable stdout buffering
    signal.signal(signal.SIGINT, player.signal_handler)

    try:
        # Iterate over autoreloaded podcasts generator
        for podcast in rac1.get_autoreloaded_podcasts():

            try:
                # Play podcast or only print command or URL
                player.play_podcast(podcast)

            except ExceptionPlayer as exc:
                # Exit with error return value 2 on error playing
                print(exc)
                return 2

    except ExceptionDownloading as exc:
        # Exit with error return value 1 on error downloading
        print(exc)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
