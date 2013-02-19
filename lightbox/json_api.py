#!/usr/bin/python
"""Lightbox library for JTAG's RGBController

This module contains the JSON-RPC web-interface for Lightbox
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '2.0'


# Standard modules
import BaseHTTPServer
import cgi
import simplejson

# Package modules
from . import utils


class ApiHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  """Ligtbox JSON API Handler."""
  def do_GET(self):
    """Very basic request router."""
    if self.path == '/':
      return self.FormRender()
    elif self.path == '/info':
      return self.ControllerInfo()
    elif self.path == '/strip':
      return self.StripInfo()
    return self.ErrorResponse('No path %r. Try the root please.' % self.path)

  def ErrorResponse(self, error):
    """Something didn't quite go as planned, let's tell the client something."""
    self.send_response(400)
    self.send_header('content-type', 'text/plain')
    self.end_headers()
    self.wfile.write(error)

  def ControllerInfo(self):
    """Returns a JSON object with controller information."""
    box = self.server.box
    box_info = {
        'controller': type(box).__name__,
        'device': box.port,
        'baudrate': box.baudrate,
        'commandrate': box.frequency,
        'outputs': len(box),
        'outputrate': float(box.frequency) / len(box)}
    self.send_response(200)
    self.send_header('content-type', 'application/json')
    self.end_headers()
    self.wfile.write(simplejson.dumps(box_info, sort_keys=True, indent='    '))

  def StripInfo(self):
    """Returns a JSON object with strip information."""
    return self.ErrorResponse('StripInfo not implemented')

  def FormRender(self, prefill=''):
    """Returns a page with a simple HTML form for manual Lightbox controls."""
    self.send_response(200)
    self.send_header('content-type', 'text/html')
    self.end_headers()
    self.wfile.write("""<html><body><form method="post">
                        <textarea name="json" cols="80" rows="30">%s</textarea>
                        <br><input type="submit" value="push!" />
                        </form></body></html>""" % HtmlEscape(prefill))

  def do_POST(self):
    """Processes Lightbox controls via JSON."""
    form = cgi.FieldStorage(
        self.rfile, self.headers, environ={'REQUEST_METHOD': 'POST'})
    try:
      json = simplejson.loads(form.getfirst('json'))
      if isinstance(json, list):
        map(self.ProcessCommand, json)
      else:
        self.ProcessCommand(json)
      return self.FormRender(form.getfirst('json'))
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
