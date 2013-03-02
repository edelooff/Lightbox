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


def ColourLovers(host, port, interval, layer):
  """Downloads color palettes from the web and displays them on the Lightbox."""
  api_address = 'http://%s:%d' % (host, port)
  while True:
    info = requests.get(api_address + '/api').json()
    outputs = info['outputCount']
    for palette in requests.get(PALETTE_FEED).json():
      # Make sure we have enough palette colors to colorize all outputs
      while len(palette['colors']) < outputs:
        palette['colors'].extend(reversed(palette['colors']))
      commands = []
      for output, color in zip(range(outputs), palette['colors']):
        commands.append({'output': output,
                         'layer': layer,
                         'color': color,
                         'opacity': 1,
                         'steps': 50})
      requests.post(api_address, data={'json': simplejson.dumps(commands)})
      print '%s: New color palette applied' % time.ctime()
      time.sleep(interval)


def main():
  """Processes commandline input to setup the API server."""
  import optparse
  parser = optparse.OptionParser()
  parser.add_option('--host', default='localhost',
                    help='Lightbox API server address (default localhost).')
  parser.add_option('--port', type='int', default=8000,
                    help='Lightbox API server port (default 8000).')
  parser.add_option('-l', '--layer', type='int', default=0,
                    help='Layer to target with color commands.')
  parser.add_option('-i', '--interval', type='int', default=60,
                    help='Time each colour swatch should be displayed.')
  options, _arguments = parser.parse_args()
  ColourLovers(options.host, options.port, options.interval, options.layer)


if __name__ == '__main__':
  main()
