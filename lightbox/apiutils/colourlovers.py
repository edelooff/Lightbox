#!/usr/bin/python
"""Lightbox JSON API Plugin for the door-state

This module contains the JSON-RPC web-interface for Lightbox
"""
__author__ = 'Lijnenspel'
__version__ = '0.2'

# Standard modules
import json
import requests
import urllib
import time

# Custom modules
from frack.projects.lightbox import utils

JSON_API = 'http://192.168.178.201:8000/'
PALETTES = ('http://www.colourlovers.com/api/'
            'palettes/top?format=json&numResults=100')


def main():
  while True:
    for palette in json.loads(requests.get(PALETTES).text):
      outputjson = []
      for channel, color in zip(range(5), palette['colors'] * 2):
        outputjson.append({'channel': channel, 'color': utils.HexToRgb(color),
                           'opacity': 1, 'steps': 50})
      data = urllib.urlencode({'json':json.dumps(outputjson)})
      try:
        requests.post("http://192.168.178.201:8000/", data=data)
        time.sleep(60)
      except requests.exceptions.ConnectionError:
        time.sleep(10)


if __name__ == '__main__':
  main()
