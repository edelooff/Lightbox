#!/usr/bin/python
"""Lightbox library for JTAG's RGBController

This module contains the JSON-RPC web-interface for Lightbox
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '2.0'


# Standard modules
import BaseHTTPServer
import cgi
import datetime
import mimetypes
import os
import simplejson
import sys

# Package modules
from . import utils


class ApiHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  """Ligtbox JSON API Handler."""
  def do_GET(self):
    """Very basic request router."""
    path = self.path
    if path == '/':
      return self._Redirect('/static/api.html')
    elif path == '/api':
      return self.ControllerInfo()
    elif path == '/api/outputs':
      return self.OutputInfo()
    elif path.startswith('/static/'):
      return self.ServeStatic()
    return self._ErrorResponse('No path %r. Try the root please.' % path)

  def _ErrorResponse(self, error):
    """Something didn't quite go as planned, let's tell the client something."""
    self.send_response(400)
    self.send_header('content-type', 'text/plain')
    self.end_headers()
    self.wfile.write(error)

  def _JsonResponse(self, data):
    """Successful request, send response to client as JSON."""
    return self._SuccessResponse(simplejson.dumps(data), 'application/json')

  def _SuccessResponse(self, data, content_type):
    """Returns a 200 OK with the given data and content-type."""
    self.send_response(200)
    self.send_header('content-type', content_type)
    self.end_headers()
    self.wfile.write(data)

  def _Redirect(self, location, code=301):
    """Redirects the client to the new location."""
    self.send_response(code)
    self.send_header('location', location)
    self.end_headers()
    self.wfile.write(location)

  def ControllerInfo(self):
    """Returns a JSON object with controller information."""
    self._JsonResponse(self.server.box.Info())

  def ServeStatic(self):
    """Returns files from the 'static' directory."""
    requested = os.path.abspath(self.path)
    if not requested.startswith('/static'):
      return self._ErrorResponse('Request not permitted: %r' % self.path)
    static_path = os.path.join(os.path.dirname(__file__), requested[1:])
    try:
      with file(static_path) as static_file:
        content_type, _encoding = mimetypes.guess_type(static_path)
        if not content_type:
          content_type = 'text/plain'
        return self._SuccessResponse(static_file.read(), content_type)
    except IOError:
      return self._ErrorResponse('File not found: %r' % self.path)

  def OutputInfo(self):
    """Returns a JSON object with Lightbox output information."""
    outputs = []
    for output_id, output in enumerate(self.server.box):
      outputs.append({
          'outputNumber': output_id,
          'mixedColorRgb': output.color,
          'mixedColorHex': '#%02x%02x%02x' % tuple(output.color),
          'layers': list(LayerReport(output))})
    self._JsonResponse(outputs)

  def do_POST(self):
    """Processes Lightbox controls via JSON."""
    if self.path != '/api':
      return self._ErrorResponse('Can only write to /api.')
    elif self.headers['content-type'] != 'application/json':
      return self._ErrorResponse('Only application/json is allowed for POST.')
    elif 'content-length' not in self.headers:
      return self._ErrorResponse('Headers must provide the message length.')
    payload = simplejson.loads(
        self.rfile.read(int(self.headers['content-length'])))
    if isinstance(payload, list):
      map(self.ProcessCommand, payload)
    else:
      self.ProcessCommand(payload)
    self.send_response(200)
    self.end_headers()

  def ProcessCommand(self, api_command):
    """Performs the given command on the Lightbox instance.

    Envelope and blend method are loaded by name from the utils module. The
    handling method is selected from a string as well, defaulting to 'Fade' if
    none is provided.
    """
    command = api_command.copy()
    if 'blender' in command:
      if command['blender'] not in utils.BLENDERS:
        raise ValueError('Provided blender %r is not a known blender.' % (
            command['blender']))
      command['blender'] = getattr(utils, command['blender'])
    if 'envelope' in command:
      if command['envelope'] not in utils.ENVELOPES:
        raise ValueError('Provided envelope %r is not a known envelope.' % (
            command['envelope']))
      command['envelope'] = getattr(utils, command['envelope'])
    channel = self.server.box[command.get('output', 0)]
    api_command['action'] = action = command.get('action', 'fade').capitalize()
    if action not in channel.ACTIONS:
      raise ValueError(
          'Chosen action %r is not an action for this channel.' %  action)
    getattr(channel, action)(**command)

  def log_message(self, format, *args):
    """Logs the messages from the RequestHandler

    This logs the requesting host (without reverse dns lookup), the time
    as ISO-8601 time string and the provided format and args.
    """
    if self.server.verbose:
      sys.stderr.write("%s - [%s] %s\n" % (
          self.client_address[0],
          datetime.datetime.now().strftime('%F %T.%f'),
          format % args))


def ApiServer(box, port=8000, quiet=False):
  """Starts and runs a JSON API server for the given Lightbox controller."""
  server = BaseHTTPServer.HTTPServer(('0.0.0.0', port), ApiHandler)
  server.box = box
  server.verbose = not quiet
  server.serve_forever()


def LayerReport(output):
  """Yields a dictionary with the state of each layer in the given output."""
  for layer in output:
    yield {'blender': layer.blender.__name__,
           'envelope': layer.envelope.__name__,
           'colorRgb': layer.color,
           'colorHex': '#%02x%02x%02x' % layer.color,
           'opacity': layer.opacity}
