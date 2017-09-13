#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Python Dependencies:
#  - httplib/http.client
#  - argparse
#  - parsedatetime
#  - datetime
#  - xml.etree.ElementTree
#  - unicodedata
#  - sys.exit
#  - subprocess
#
# Other dependencies:
#  - mplayer (shell command)
#

from __future__ import print_function
from pprint import pprint
from subprocess import call,PIPE
from sys import exit,stdout

'''
    File name: Rac1.py
    Author: Emilio del Giorgio
    Date created: 4/7/2017
    Date last modified: 4/7/2017
    Python Version: 3 / 2.7
'''

__author__ = "Emilio del Giorgio"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = __author__
__email__ = "emidaruma@gmail.com"
__status__ = "Production"


def isint(value):
   '''Detect if a string has an integer value and returns boolean'''
   
   try:
      int(value)
      return True
   except:
      return False


def parse_my_args():
   '''Parse ARGv and return arg object'''
   
   from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter,RawDescriptionHelpFormatter
   
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
      
      import unicodedata
      
      for exc in args.exclude:
         if isint(exc):
            excludes.append( exc )
         else:
            try:
               # Py 2
               excludes.extend( unicodedata.normalize('NFKD',exc.decode('utf8')).encode('ascii', 'ignore').upper().split(',') )
            except:
               # Py 3
               excludes.extend( unicodedata.normalize('NFKD',exc).upper().split(',') )
   
   # L'afegim al args
   setattr(args, 'excludes', excludes)
   
   # Return arguments and excludes
   return args


def parse_my_date(date_arg):
   '''Parse date and return a DD-MM-YY string'''
   
   # Can parse human-like dates, like 'date' command
   import parsedatetime as pdt # $ pip install parsedatetime
   from datetime import datetime

   cal = pdt.Calendar()
   now = datetime.now()
   
   # Get date from string
   date = cal.parseDT(date_arg, now)[0]
   
   # Return date parsed as DD-MM-YY
   return date.strftime('%d-%m-%y')
   

def get_rac1_xml(date):
   '''Download XML with podcasts feed and returns text/xml data into string'''
   
   # HTTP
   try:
      # Py 2
      import httplib
   except:
      # Py 3
      import http.client as httplib
   
   # TODO: Al tanto! Alternativa que parece funcionar mejor:
   # wget -O - "http://www.rac1.cat/audioteca/a-la-carta/cerca?text=&sectionId=HOUR&from=24%2F07%2F2017&to=" | grep 'http://audio.rac1.cat'
   # (echo '<xml>\n'; cat test; echo '</xml>' ) | egrep -v '<input|<i class|<iframe' | sed -e 's/\?source=WEB&download//g' | xml2
   
   # http://www.rac1.cat/audioteca/rss/el-mon/HOUR
   
   # {} must be in format DD-MM-YY
   URL_HOST="www.racalacarta.com:80"
   URL_GET="/wp-feeder.php?param={}&is_date=1&action=read_dir&limit=30"
   
   print("Descarreguem Feed XML del llistat de Podcasts amb data {}: {}{}".format(date, URL_HOST, URL_GET.format(date)))

   conn = httplib.HTTPConnection(URL_HOST)
   conn.request("GET", URL_GET.format(date))
   response = conn.getresponse()
   
   data = response.read()
   conn.close()
   
   # OK
   if response.status == 200:
      return response.status, data
   
   # KO
   return response.status, response.reason


def print_xml_recursive(element, level=0):
   '''Debug: Print XML object tree'''
   
   for child in element:
      print("   " * level, '*', child.tag, child.attrib, child.text)
      print_recursive(child, level=level + 1)


def parse_my_xml(data):
   '''Parse XML data and return podcasts list in hour ascending order'''

   from xml.etree import ElementTree as ET

   root = ET.fromstring(data)
   #print_xml_recursive(root)
   
   list = []
   for item in root.iter('item'):
   
      # Get info from item childs
      title = item.find('title').text
      link = item.find('link').text
      description = item.find('description').text
      enclosure = item.find('enclosure')
      
      # Separem la descripció en espais (Emis.: 03-07-17 a les 01h): split
      # Agafem l'últim element (08h): [-1]
      # Traiem l'últim char (08): [:-1]
      hora = description.split(' ')[-1][:-1]
      
      # Append that info into the list
      list.append(dict(
         title=title.split('(')[0].strip(), 
         link=link, 
         description=description, 
         length="{}".format(int(int(enclosure.attrib['length']) / 1024)),
         hora=int(hora)
      ))
   
   # Return the list in reverse order
   return list[::-1]


def get_podcasts_list(date):
   ''' 
   Get list of podcasts from predefined URL
   
     - Using human readable dates (already normalized in parse_my_args)
     - From HTTP connection
     - Parxe XML
   '''
   
   # HTTP
   status, data = get_rac1_xml(date)
   
   if status != 200:
      print("Error intentant descarregar el XML amb el llistat de podcasts: {}: {}".format(status, data))
      exit(1)
   
   # XML
   return parse_my_xml(data)
   

mplayer_process = None
def play_podcast(podcast, only_print=False, start='0'):
   '''Play a podcast with mplayer, or only print the command'''
   
   global mplayer_process
   
   call_args = ["mplayer", "-cache-min", "1", "-cache", podcast['length'], "-ss", start, podcast['link']]
   
   # Print?
   if only_print == True:

      # Add quotes to link argument
      print_args = call_args[:]
      print_args[-1] = '"{}"'.format(podcast['link'])
      
      print(*print_args, sep=" ")
      return
      
   print('### Escoltem "{}" {}h: {}'.format(podcast['title'], podcast['hora'], podcast['link']))
   
   # Posem el títol a l'intèrpret de comandes
   print("\x1B]2;{} {}h\x07".format(podcast['title'], podcast['hora']))
   
   # Listen with mplayer
   # Use try to catch CTRL+C correctly
   try:
      mplayer_process = call(call_args)
   except:
      exit(2)
   
   return 0


def play_all_podcasts(args, done_last=0):
   '''Play all podcasts from desired list using args. Returns number of podcasts played.'''

   # Get list of podcasts:
   #  - Using human readable dates (already parsed at parse_my_args)
   #  - From HTTP connection (done via get_podcasts_list)
   #  - Parxe XML (done via get_podcasts_list)
   podcasts = get_podcasts_list(args.date)[done_last:]
   
   #
   # Iterate, filter and play podcasts list
   #
   done = 0
   for podcast in podcasts:
   
      play = True

      # From and To hours
      if not (args.from_hour <= podcast['hora'] <= args.to_hour):
         play = False

      # Exclusions
      else:
         for exc in args.excludes:
            if ( isint(exc) and int(exc) == podcast['hora'] ) or str(exc) in podcast['title'] :
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


def signal_handler(sign, frame):
   '''Exits cleanly'''
   
   import psutil, time

   # Flush stdout and wait until mplayer exits completely
   stdout.flush()
   print('CTRL-C!! Sortim!')
   
   time.sleep(1)
   
   global mplayer_process
   
   if mplayer_process != None:
      print("Waiting for mplayer to finish...")
      
      process = psutil.Process(mplayer_process.pid)
      
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
   stdout = fdopen(stdout.fileno(), 'w', 0)

   # Parse ARGv
   args = parse_my_args()
   
   # Play until none podcast is played
   # This will ensure re-download of XML list when we begin to play
   # before last podcast is listed in the XML Feed
   done_last = 0
   
   while True:
      done = play_all_podcasts(args, done_last=done_last)
      done_last += done
      
      if done == 0:
         exit(0)
   
