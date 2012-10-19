#!/usr/bin/python
"""Lightbox JSON API Plugin for the door-state

This module contains the JSON-RPC web-interface for Lightbox
"""
__author__ = 'Lijnenspel'
__version__ = '0.3'

# Standard modules
import simplejson
import time
import urllib2

# Custom modules
from frack.projects.lightbox import utils

JSON_API = 'http://192.168.178.201:8000/'
PALETTE_URL = ('http://www.colourlovers.com/api/'
               'palettes/top?format=json&numResults=100')


def main():
  while True:
    for palette in simplejson.loads(urllib2.urlopen(PALETTE_URL).read()):
      commands = []
      for channel, color in zip(range(5), palette['colors'] * 2):
        commands.append({'channel': channel, 'color': utils.HexToRgb(color),
                         'opacity': 1, 'steps': 50})
      utils.SendApiCommand(JSON_API, commands)
      time.sleep(60)


if __name__ == '__main__':
  main()
