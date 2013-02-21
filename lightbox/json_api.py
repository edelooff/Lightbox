#!/usr/bin/python
"""Lightbox library for JTAG's RGBController

This module contains the JSON-RPC web-interface for Lightbox
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '2.0'


# Standard modules
import BaseHTTPServer
import cgi
import os
import simplejson

# Package modules
from . import utils


class ApiHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  """Ligtbox JSON API Handler."""
  def do_GET(self):
    """Very basic request router."""
    path, _sep, query = self.path.partition('?')
    params = dict(cgi.parse_qsl(query))
    if path == '/':
      return self.FormRender()
    elif path == '/api':
      return self.ControllerInfo()
    elif path == '/api/output':
      return self.OutputInfo(params)
    return self.ErrorResponse('No path %r. Try the root please.' % path)

  def ErrorResponse(self, error):
    """Something didn't quite go as planned, let's tell the client something."""
    self.send_response(400)
    self.send_header('content-type', 'text/plain')
    self.end_headers()
    self.wfile.write(error)

  def HtmlResponse(self, data):
    """Successful request, send a response to the client as HTML."""
    self.send_response(200)
    self.send_header('content-type', 'text/html')
    self.end_headers()
    self.wfile.write(data)

  def JsonResponse(self, data):
    """Successful request, send response to client as JSON."""
    self.send_response(200)
    self.send_header('content-type', 'application/json')
    self.end_headers()
    self.wfile.write(simplejson.dumps(data))

  def ControllerInfo(self):
    """Returns a JSON object with controller information."""
    box = self.server.box
    self.JsonResponse({
        'controller': type(box).__name__,
        'device': box.serial.port,
        'baudrate': box.serial.baudrate,
        'commandrate': box.frequency,
        'outputs': len(box),
        'outputrate': float(box.frequency) / len(box)})

  def OutputInfo(self, params):
    """Returns a JSON object with Lightbox output information."""
    if 'id' not in params:
      return self.ErrorResponse('An argument "id" should be provided')
    if not params['id'].isdigit():
      return self.ErrorResponse('Output id should be a number.')
    output_id = int(params['id'])
    if not 0 <= output_id < len(self.server.box):
      return self.ErrorResponse('Output id out of bounds')
    output = self.server.box[output_id]
    self.JsonResponse({
        'outputNumber': output.output_id,
        'mixedColorRgb': output.color,
        'mixedColorHex': '#%02x%02x%02x' % tuple(output.color),
        'layerCount': len(output.layers),
        'layers': list(LayerReport(output))})

  def FormRender(self, prefill=''):
    """Returns a page with a simple HTML form for manual Lightbox controls."""
    form_path = os.path.join(os.path.dirname(__file__), 'api.html')
    with file(form_path) as form_page:
      return self.HtmlResponse(form_page.read() % HtmlEscape(prefill))

  def do_POST(self):
    """Processes Lightbox controls via JSON."""
    if self.path not in ('/', '/api'):
      return self.ErrorResponse('No path %r. Try the root please.' % path)
    form = cgi.FieldStorage(
        self.rfile, self.headers, environ={'REQUEST_METHOD': 'POST'})
    try:
      json = simplejson.loads(form.getfirst('json'))
      if isinstance(json, list):
        map(self.ProcessCommand, json)
      else:
        self.ProcessCommand(json)
      if self.path == '/':
        form_content = simplejson.dumps(json, sort_keys=True, indent='  ')
        return self.FormRender(form_content)
    except Exception, error:
      return self.ErrorResponse(str(error))

  def ProcessCommand(self, command):
    """Performs the given command on the Lightbox instance.

    Envelope and blend method are loaded by name from the utils module. The
    handling method is selected from a string as well, defaulting to 'Fade' if
    none is provided.
    """
    if 'blender' in command:
      command['blender'] = getattr(utils, command['blender'])
    if 'envelope' in command:
      command['envelope'] = getattr(utils, command['envelope'])
    channel = self.server.box[command.pop('channel', 0)]
    action = getattr(channel, command.pop('action', 'fade').capitalize())
    action(**command)


def ApiServer(box, port=8000):
  """Starts and runs a JSON API server for the given Lightbox controller."""
  server = BaseHTTPServer.HTTPServer(('0.0.0.0', port), ApiHandler)
  server.box = box
  server.serve_forever()


def HtmlEscape(text):
  """Prevent XSS problems bij escaping the 5 characters that cause trouble."""
  text = text.replace('&', '&amp;')
  text = text.replace('"', '&quot;')
  text = text.replace("'", '&#39;')  # &apos; is valid, but poorly supported.
  text = text.replace('>', '&gt;')
  return text.replace('<', '&lt;')


def LayerReport(output):
  """Yields a dictionary with the state of each layer in the given output."""
  for layer in output:
    yield {'blender': layer.blender.__name__,
           'envelope': layer.envelope.__name__,
           'colorRgb': layer.color,
           'colorHex': '#%02x%02x%02x' % layer.color,
           'opacity': layer.opacity}
