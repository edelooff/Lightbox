#!/usr/bin/python
"""Minimal application to set up a Lightbox JSON API server."""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '2.0'

# Custom modules
from lightbox import controller
from lightbox import json_api


def StartLightboxApi(name, port):
  """Starts a Lightbox API service.

  The provided controller name should be a class of the controller module. An
  instance of this will be created to use for the JSON API. The server will
  listen on the provided port number.
  """
  print 'Initiating controller %r ...' % name
  ctrl_obj = getattr(controller, name).ConnectFirst()
  print 'Starting API server on port %d ...' % port
  json_api.ApiServer(ctrl_obj, port=port)


def main():
  """Processes commandline input to setup the API server."""
  import optparse
  parser = optparse.OptionParser()
  parser.add_option('-c', '--controller', dest='name',
                    default='JTagController',
                    help='Controller class to instantiate.')
  parser.add_option('-p', '--port', type='int', dest='port', default=8000,
                    help='Port to run the Lightbox API on.')
  options, _arguments = parser.parse_args()
  StartLightboxApi(**vars(options))


if __name__ == '__main__':
  main()
