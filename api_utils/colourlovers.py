#!/usr/bin/python
"""Lightbox JSON API Plugin for the door-state

This module contains the JSON-RPC web-interface for Lightbox
"""
__author__ = 'Lijnenspel'
__version__ = '0.4'

# Standard modules
import requests
import simplejson
import time

JSON_API = 'http://localhost:8000/'
PALETTE_URL = ('http://www.colourlovers.com/api/'
               'palettes/top?format=json&numResults=100')

def HexToRgb(hex_color):
  colors = hex_color[:2], hex_color[2:4], hex_color[4:]
  return tuple(int(color, 16) for color in colors)


def main():
  while True:
    for palette in requests.get(PALETTE_URL).json:
      commands = []
      for channel, color in zip(range(5), palette['colors'] * 2):
        commands.append({'channel': channel,
                         'color': HexToRgb(color),
                         'opacity': 1,
                         'steps': 50})
      requests.post(JSON_API, data={'json': simplejson.dumps(commands)})
      time.sleep(60)


if __name__ == '__main__':
  main()
