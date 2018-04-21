#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Rac1.py: listen to Rac1 catalan radio station from its public podcasts
#
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
#  - httplib/http.client
#  - argparse
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
from pprint import pprint
from subprocess import call, PIPE, CalledProcessError
from sys import exit,stdout
import re, json, unicodedata

# HTTP
try:
   # Py 2
   import httplib
except:
   # Py 3
   import http.client as httplib


'''
    File name: Rac1.py
    Author: Emilio del Giorgio
    Date created: 4/7/2017
    Date last modified: 8/12/2017
    Python Version: 3 / 2.7
'''

__author__ = "Emilio del Giorgio"
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = __author__
__email__ = "emidaruma@gmail.com"
__status__ = "Production"


def isint(value):
   '''Detect if a string has an integer value and returns the result as boolean'''
   
   try:
      int(value)
      return True
   except:
      return False


def normalize_encoding_upper(str):
   '''Normalizes a binary string to an upper non-accented one'''
   
   try:
      # Py 2
      str = unicodedata.normalize('NFKD',str.decode('utf8')).encode('ascii', 'ignore').upper()
   except:
      # Py 3
      str = unicodedata.normalize('NFKD',str).upper()
   
   return str


def parse_my_args():
   '''Parse ARGv and return arg object'''
   
   from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter
   
   # Permet mostrar l'epilog amb la llista ben formatada, mentre es 
   # mostren els arguments i els seus defaults formatats correctament
   # https://stackoverflow.com/questions/18462610/argumentparser-epilog-and-description-formatting-in-conjunction-with-argumentdef
   class MyCustomFormatter(ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter):
      pass

   parser = ArgumentParser(
               description="Escolta els podcasts de Rac1 sequencialment i sense interrupcions",
               formatter_class=MyCustomFormatter,
               epilog="Nota: Mentre estàs escoltant un podcast, pots passar al següent\n"
                      "prement les tecles [ENTER] o [q].\n\n"
                      "Pots sortir del tot prement CTRL+C\n\n"
                      "Pots tirar endavant i endarrere amb les tecles:\n"
                      "   - De direccions esquerra/dreta (10s)\n"
                      "   - De direccions amunt/avall (1m)\n"
                      "   - De Pàgina amunt/avall (10m)\n"
                      )
   
   parser.add_argument("-p", "--print", 
                       dest='only_print', 
                       default=False,
                       action="store_true",
                       help="Només mostra el que s'executaria.")
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
                       help="El moment en que cal començar el primer podcast, amb el format de l'opció '-ss' del mplayer.")
   parser.add_argument("-x", "--exclude", 
                       dest='exclude',
                       metavar="EXCLUDE1[,EXCLUDE2...]",
                       default=['SEGONA HORA,PRIMER TOC'],
                       action="append",
                       help="Programes a excloure, per hora o nom, separats per coma i/o en diverses aparicions de '-x'.")
   parser.add_argument("-c", "--clean-exclude", 
                       dest='exclude',
                       action='store_const',
                       const=[],
                       help="Neteja la llista d'exclusions definida fins el moment. No afecta posteriors entrades de '-x'.")

   # Parse arguments
   args = parser.parse_args()
   
   # Normalize Date
   setattr(args, 'date', parse_my_date(args.date))
   
   # Normalize excludes: uppercase with no accents, splited by comma into one-dimensional array
   excludes = []
   if len(args.exclude) > 0:
      
      for exc in args.exclude:
      
         # Exclude by hour
         if isint(exc):
            excludes.append( exc )
            
         # Exclude by name
         else:
            excludes.extend( normalize_encoding_upper(exc).split(',') )
   
   # L'afegim al args
   setattr(args, 'excludes', excludes)
   
   # Return arguments and excludes
   return args


def parse_my_date(date_arg):
   '''Parse date and return a DD/MM/YYYY string'''
   
   # Can parse human-like dates, like 'date' command
   import parsedatetime as pdt # $ pip install parsedatetime
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
   

def get_page(URL_HOST, URL_GET, https=False):
   '''Downloads a page'''
   
   # Connect to server, send request and get response
   if not https:
      conn = httplib.HTTPConnection(URL_HOST)
   else:
      conn = httplib.HTTPSConnection(URL_HOST)
      
   headers = {
      'User-Agent': "github.com/emibcn/Rac1.py",
      'Cache-Control': 'max-age=0',
      'Connection': 'keep-alive',
      'DNT': '1',
      'Upgrade-Insecure-Requests': '1',
   }
   conn.request("GET", URL_GET, None, headers)
   response = conn.getresponse()
   
   # Get data from response and close connection
   data = response.read()
   conn.close()
   
   # OK
   if response.status == 200:
      return response.status, data
   
   reason = response.reason
   
   if response.status in [300, 301, 302]:
      location = response.getheader("Location")
      
      if len(location) > 0:
         reason += ": %s" % (location)
      
   # KO
   return response.status, reason


def get_rac1_page(date, page=0):
   '''Download HTML with audio UUIDs'''
   
   # TODO: Al tanto! Alternativa que parece funcionar mejor:
   # wget -O - "http://www.rac1.cat/audioteca/a-la-carta/cerca?text=&sectionId=HOUR&from=24%2F07%2F2017&to=" | grep 'http://audio.rac1.cat'
   # (echo '<xml>\n'; cat test; echo '</xml>' ) | egrep -v '<input|<i class|<iframe' | sed -e 's/\?source=WEB&download//g' | xml2
   #
   # wget -q -O - "http://www.rac1.cat/audioteca/a-la-carta/cerca?text=&programId=&sectionId=HOUR&from=24%2F09%2F2017&to=&pageNumber=0" | \
   #    egrep 'data-audio-id|data-audioteca-search-page' | \
   #    sed -e 's/^.* \(data-[^=]*\)="\([^"]*\)".*$/\1=\2/g'
   
   # http://www.rac1.cat/audioteca/rss/el-mon/HOUR
   
   # {date} must be in format DD/MM/YYYY
   URL_HOST="www.rac1.cat"
   URL_GET="/a-la-carta/cerca?text=&programId=&sectionId=HOUR&from={date}&to={date}&pageNumber={page}&btn-search="
   
   print(u"Descarreguem Feed HTML del llistat de Podcasts amb data {date}: {url}{get}".format(date=date, url=URL_HOST, get=URL_GET.format(date=date, page=page)))
   
   # Return downloaded page
   return get_page(URL_HOST, URL_GET.format(date=date, page=page), https=True)


def parse_rac1_data(data):
   '''Parse Rac1 data and return podcasts list in hour ascending order'''
   
   my_re = re.compile(r'^.* (data-[^=]*)="([^"]*)".*$')
   
   # Parse response:
   # - Filter lines containing data-audio-id or data-audioteca-search-page
   # - Decode from binary utf-8 to string
   # - Only get values for data-* HTML attributes, without quotes
   list = [ re.sub(my_re, r'\1=\2', line.decode('utf-8')) \
              for line in data.split(b'\n') 
                 if b'data-audio-id' in line \
                    or b'data-audioteca-search-page' in line ]
   
   # Filter results by type
   audio_uuid_list = [ line for line in list if 'data-audio-id' in line ]
   pages_list      = [ line for line in list if 'data-audioteca-search-page' in line ]
   
   # Return segregated lists
   return audio_uuid_list, pages_list


def get_audio_uuids(date):
   '''Get full day audio UUIDs list'''
   
   # Download date's first page
   status, data = get_rac1_page(date)
   
   if status != 200:
      print(u"Error intentant descarregar la pàgina HTML amb el llistat de podcasts: {}: {}".format(status, data))
      exit(1)
   
   # Parse downloaded data, getting UUIDs initial list and pages list
   audio_uuid_list, pages_list = parse_rac1_data(data)
   
   # Get extra pages, if needed
   # [1:] : remove first page, as it has already been downloaded
   for page in pages_list[1:]:
      
      # Get page number
      _, p = page.split('=')
      
      # Download page uuids
      status, data = get_rac1_page(date, p)
      
      if status != 200:
         print(u"Error intentant descarregar la pàgina HTML amb el llistat de podcasts: {}: {}".format(status, data))
         exit(1)
      
      # Parse page data
      audio_uuid_list_page, _ = parse_rac1_data(data)
      
      # Add audio UUIDs to the list
      audio_uuid_list += audio_uuid_list_page
   
   # Return only each audio's UUID
   return [ varval.split('=')[1] for varval in audio_uuid_list ]


def get_podcast_data(uuid):
   '''Download podcast information by its UUID'''
   
   URL_HOST="api.audioteca.rac1.cat"
   URL_GET="/piece/audio?id={uuid}"
   
   # Download podcast JSON data
   status, data_raw = get_page(URL_HOST, URL_GET.format(uuid=uuid), https=True)

   if status != 200:
      print(u"Error intentant descarregar el JSON amb les dades del podcast: {}: {}".format(status, data_raw))
      exit(1)
   
   # Parse JSON data
   data = json.loads(data_raw.decode('utf-8'))
   
   # Parse the hour
   data['audio']['hour'] = int(data['audio']['time'].split(':')[0])
   
   # Return parsed data
   return data
   

def get_podcasts_list(date):
   ''' 
   Get list of podcasts from predefined URL
   
     - Using human readable dates (already normalized in parse_my_args)
     - From HTTP connection
     - Parse HTTP and JSON
   '''
   
   # Get all day audio UUIDs
   podcasts_list = [ get_podcast_data(uuid) for uuid in get_audio_uuids(date) ]
   
   # DEBUG
   #pprint([ [podcast['audio']['time'], podcast['path']] for podcast in podcasts_list ])
   #pprint(podcasts_list)
   #exit(0)
   
   # Return the list in reverse order
   return podcasts_list[::-1]


mplayer_process = None
def play_podcast(podcast, only_print=False, start='0'):
   '''Play a podcast with mplayer, or only print the command'''
   
   global mplayer_process
   
   # Cache:
   #  - Try to play as soon as possible
   #  - Try to download full podcast from the beginning (full cache)
   call_args = ["mplayer", "-cache-min", "1", "-cache", str(podcast['durationSeconds'] * 10), "-ss", start, podcast['path']]
   
   # Print?
   if only_print == True:

      # Add quotes to link argument
      print_args = call_args[:]
      print_args[-1] = '"{}"'.format(podcast['path'])
      
      # Print execution line
      print(*print_args, sep=" ")
      return
      
   print(u'### Escoltem "{}" {}h: {}'.format(podcast['audio']['title'], podcast['audio']['hour'], podcast['path']))
   
   # Posem el títol a l'intèrpret de comandes
   print(u"\x1B]2;{} {}h\x07".format(podcast['audio']['title'], podcast['audio']['hour']))
   
   # Listen with mplayer
   # Use try to catch CTRL+C correctly
   try:
      mplayer_process = call(call_args)
   except CalledProcessError as e:
      print(u"ERROR: " + e.output)
      exit(2)
   
   return 0


def play_all_podcasts(args, done_last=0):
   '''Play all podcasts from desired list using args. Returns number of podcasts played.'''

   # Get list of podcasts:
   #  - Using human readable dates (already parsed at parse_my_args)
   #  - From HTTP connection (done via get_podcasts_list)
   #  - Parse XML (done via get_podcasts_list)
   podcasts = get_podcasts_list(args.date)[done_last:]
   
   #
   # Iterate, filter and play podcasts list
   #
   done = 0
   for podcast in podcasts:
   
      play = True

      # From and To hours
      if not (args.from_hour <= podcast['audio']['hour'] <= args.to_hour):
         play = False

      # Exclusions
      else:
         for exc in args.excludes:
            
            # Exclude by hour and by name
            if ( isint(exc) and int(exc) == podcast['audio']['hour'] ) or \
                  str(exc) in normalize_encoding_upper( podcast['audio']['title'] ) :
               play = False
               break
      
      # Si l'hem d'escoltar
      if play:
         
         # Si és el primer, apliquem el FastForward inicial
         if (done + done_last) == 0:
            play_podcast(podcast, only_print=args.only_print, start=args.start_first)
         else:
            play_podcast(podcast, only_print=args.only_print)
         
      done += 1
   
   # Return podcasts done
   return done

already_exiting = False
def signal_handler(sign, frame):
   '''Exits cleanly'''
   
   # Don't begin exit process more than once
   global already_exiting
   if already_exiting:
      return
   
   already_exiting = True
   
   # Flush stdout and wait until mplayer exits completely
   stdout.flush()
   print(u'CTRL-C!! Sortim!')
   
   # Wait a second...
   import time
   time.sleep(1)
   
   global mplayer_process
   
   # If mplayer process is defined
   if mplayer_process is not None:
      print(u"Waiting for mplayer to finish...")
      
      import psutil
      
      try:
         # Get process info
         process = psutil.Process(mplayer_process)
      except:
         print(u"MPlayer already ended.")
      else:
         print(u"Killing MPlayer and all possible childs.")
         
         # Kill mplayer childs and wait for them to exit completely
         for proc in process.children(recursive=True):
            proc.send_signal(SIGTERM)
            proc.wait()

         # Kill mplayer and wait for it to exit completely
         process.send_signal(SIGTERM)
         process.wait()
   
   # Reset terminal
   #subprocess.Popen(['reset']).wait()
   
   exit(3)


if __name__ == "__main__":
   '''Parses arguments, gets podcasts list and play its items according to arguments'''
   
   # Borrow SIGINT to exit cleanly and disable stdout buffering
   from signal import signal,SIGINT
   from os import fdopen

   signal(SIGINT, signal_handler)
   
   # Only Py2
   #stdout = fdopen(stdout.fileno(), 'w', 0)

   # Parse ARGv
   args = parse_my_args()
   
   # Play until none podcast is played
   # This will ensure re-download of XML list when we begin to play
   # before last podcast is listed in the XML Feed
   done_last = 0
   
   while True:
      done = play_all_podcasts(args, done_last=done_last)
      done_last += done
      
      # If we could not play anything, don't try to download 
      # the list again: there will be nothing, again
      if done == 0:
         exit(0)
