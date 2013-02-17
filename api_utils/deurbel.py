#!/usr/bin/python
"""Lightbox JSON API Plugin for the door-state

This module contains the JSON-RPC web-interface for Lightbox
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '0.3'

# Standard modules
import requests
import simplejson
import sys

# Custom modules
from frack.libs.announce import transponder

JSON_API = 'http://localhost:8000/'

def SpaceClosed():
  acts = []
  for chan in range(5):
    acts.append({'channel': chan, 'layer': 2, 'opacity': 0,
                 'color': (255, 0, 0), 'steps': 1, 'blender': 'LabAverage'})
    acts.append({'channel': chan, 'layer': 2, 'opacity': 1, 'steps': 120})
    acts.append({'channel': chan, 'layer': 2, 'color': (0, 0, 0), 'steps': 120})
  requests.post(JSON_API, data={'json': simplejson.dumps(acts)})


def SpaceOpened():
  acts = []
  for chan in range(5):
    acts.append({'channel': chan, 'layer': 2, 'color': (0, 0, 0), 'steps': 1})
    acts.append({'channel': chan, 'layer': 2, 'color': (0, 255, 0), 'steps': 120})
    acts.append({'channel': chan, 'layer': 2, 'opacity': 0, 'steps': 120})
  requests.post(JSON_API, data={'json': simplejson.dumps(acts)})


def main(proxy=False):
  if proxy:
    receiver = transponder.ProxyReceiver()
  else:
    receiver = transponder.Receiver()
  for announce in receiver:
    if announce['domain_global'] == 0 and announce['domain_local'] == 0:
      if announce['message'][0] == 'opened':
        SpaceOpened()
      else:
        SpaceClosed()


if __name__ == '__main__':
  if len(sys.argv) > 1:
    if sys.argv[1] == "proxy":
      main(proxy=True)
    else:
      print "Usage: %s [proxy]" % sys.argv[0]
  else:
    main()
