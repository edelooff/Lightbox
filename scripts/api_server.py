#!/usr/bin/python
"""Minimal application to set up a Lightbox JSON API server."""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '2.0'

# Custom modules
from lightbox import controller
from lightbox import json_api


def StartLightboxApi(controller_name, port, outputs, quiet):
  """Starts a Lightbox API service.

  The provided controller name should be a class of the controller module. An
  instance of this will be created to use for the JSON API. The server will
  listen on the provided port number.
  """
  print 'Initiating controller %r ...' % controller_name
  ctrl_obj = getattr(controller, controller_name).FirstDevice(outputs=outputs)
  print 'Starting API server on http://localhost:%d/ ...' % port
  json_api.ApiServer(ctrl_obj, port=port, quiet=quiet)


def main():
  """Processes commandline input to setup the API server."""
  import optparse
  import sys
  parser = optparse.OptionParser()
  parser.add_option('-c', '--controller', default='NewController',
                    help='Controller class to instantiate.')
  parser.add_option('-o', '--outputs', type='int', default=5,
                    help='Number of outputs to use on the hardware.')
  parser.add_option('-p', '--port', type='int', default=8000,
                    help='Port to run the Lightbox API on.')
  parser.add_option('-q', '--quiet', action='store_true', default=False,
                    help='Disables request logging to stderr.')
  options, _arguments = parser.parse_args()
  try:
    StartLightboxApi(
        options.controller, options.port, options.outputs, options.quiet)
  except controller.ConnectionError:
    sys.exit('ABORT: Could not find a suitable device.')


if __name__ == '__main__':
  main()
