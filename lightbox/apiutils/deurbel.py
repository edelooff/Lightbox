#!/usr/bin/python
"""Lightbox JSON API Plugin for the door-state

This module contains the JSON-RPC web-interface for Lightbox
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '0.1'

# Standard modules
import urllib
import urllib2
import simplejson

# Custom modules
from frack.libs.announce import transponder

JSON_API = 'http://192.168.178.201:8000/'


def SpaceClosed():
  acts = []
  for chan in range(5):
    acts.append({'channel': chan, 'layer': 2, 'opacity': 0,
                 'color': (255, 0, 0), 'steps': 1, 'blender': 'LabAverage'})
    acts.append({'channel': chan, 'layer': 2, 'opacity': 1, 'steps': 60})
    acts.append({'channel': chan, 'layer': 2, 'color': (0, 0, 0), 'steps': 60})
  json = simplejson.dumps(acts)
  urllib2.urlopen(JSON_API, data=urllib.urlencode({'json': json}))


def SpaceOpened():
  acts = []
  for chan in range(5):
    acts.append({'channel': chan, 'layer': 2, 'color': (0, 0, 0), 'steps': 1})
    acts.append({'channel': chan, 'layer': 2, 'color': (0, 255, 0), 'steps': 60})
    acts.append({'channel': chan, 'layer': 2, 'opacity': 0, 'steps': 60})
  json = simplejson.dumps(acts)
  urllib2.urlopen(JSON_API, data=urllib.urlencode({'json': json}))


def main():
  for announce in transponder.Receiver():
    if announce['domain_global'] == 0 and announce['domain_local'] == 0:
      try:
        if announce['message'][0] == 'opened':
          SpaceOpened()
        else:
          SpaceClosed()
      except urllib2.HTTPError:
        pass


if __name__ == '__main__':
  main()
