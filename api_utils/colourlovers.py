#!/usr/bin/python
"""Lightbox JSON API Plugin to provide pleasing color palettes.

This application interacts with the JSON API for Lightbox.
"""
__author__ = 'Lijnenspel'
__version__ = '0.4'

# Standard modules
import requests
import simplejson
import time

PALETTE_FEED = ('http://www.colourlovers.com/api/'
                'palettes/top?format=json&numResults=100')

def HexToRgb(hex_color):
  """Converts a hex-color string to an RGB tuple."""
  colors = hex_color[:2], hex_color[2:4], hex_color[4:]
  return tuple(int(color, 16) for color in colors)


def ColourLovers(host, port, interval):
  api_address = 'http://%s:%d' % (host, port)
  while True:
    for palette in requests.get(PALETTE_FEED).json:
      commands = []
      for channel, color in zip(range(5), palette['colors'] * 2):
        commands.append({'channel': channel,
                         'color': HexToRgb(color),
                         'opacity': 1,
                         'steps': 50})
      requests.post(api_address, data={'json': simplejson.dumps(commands)})
      time.sleep(interval)


def main():
  """Processes commandline input to setup the API server."""
  import optparse
  parser = optparse.OptionParser()
  parser.add_option('--host', default='localhost',
                    help='Lightbox API server address (default localhost).')
  parser.add_option('--port', type='int', default=8000,
                    help='Lightbox API server port (default 8000).')
  parser.add_option('-i', '--interval', type='int', default=60,
                    help='Time each colour swatch should be displayed.')
  options, _arguments = parser.parse_args()
  ColourLovers(options.host, options.port, options.interval)


if __name__ == '__main__':
  main()
