#!/usr/bin/python
"""Lightbox JSON API Plugin for the door-state

This application interacts with the JSON API for Lightbox.
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '0.5'

# Standard modules
import requests
import simplejson

# Custom modules
from frack.libs.announce import transponder


def SpaceClosed(channels):
  """Animation to play when the space closes."""
  for chan in range(channels):
    yield {'channel': chan, 'layer': 2, 'opacity': 0,
           'color': (255, 0, 0), 'steps': 1, 'blender': 'LabAverage'}
    yield {'channel': chan, 'layer': 2, 'opacity': 1, 'steps': 120}
    yield {'channel': chan, 'layer': 2, 'color': (0, 0, 0), 'steps': 120}


def SpaceOpened(channels):
  """Animation to play when the space opens."""
  for chan in range(channels):
    yield {'channel': chan, 'layer': 2, 'color': (0, 0, 0), 'steps': 1}
    yield {'channel': chan, 'layer': 2, 'color': (0, 255, 0), 'steps': 120}
    yield {'channel': chan, 'layer': 2, 'opacity': 0, 'steps': 120}


def SpaceStateIndicator(host, port, proxy=False):
  """Listens for SpaceAnnounces and plays animations on space-state changes."""
  api_address = 'http://%s:%d' % (host, port)
  receiver = transponder.ProxyReceiver() if proxy else transponder.Receiver()
  for announce in receiver:
    if announce['domain_global'] == 0 and announce['domain_local'] == 0:
      if announce['message'][0] == 'opened':
        commands = list(SpaceOpened(5))
      else:
        commands = list(SpaceClosed(5))
      requests.post(api_address, data={'json': simplejson.dumps(commands)})


def main():
  """Processes commandline input to setup the API server."""
  import optparse
  parser = optparse.OptionParser()
  parser.add_option('--host', default='localhost',
                    help='Lightbox API server address (default localhost).')
  parser.add_option('--port', type='int', default=8000,
                    help='Lightbox API server port (default 8000).')
  parser.add_option('--proxy', actin='store_true', default=False,
                    help=('Connects through an Announce proxy instead of '
                          'setting up a UDP listener directly.'))
  options, _arguments = parser.parse_args()
  SpaceStateIndicator(options.host, options.port, options.proxy)


if __name__ == '__main__':
  main()
