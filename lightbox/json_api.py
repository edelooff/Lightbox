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
  def do_GET(self):
    self.send_response(200)
    self.send_header('content-type', 'text/html')
    self.end_headers()
    self.wfile.write("""<html><body><form method="post">
                        <textarea name="json" cols="80" rows="30"></textarea>
                        <input type="submit" value="push!" />
                        </form></body></html>""")

  def do_POST(self):
    form = cgi.FieldStorage(
        self.rfile, self.headers, environ={'REQUEST_METHOD': 'POST'})
    try:
      json = simplejson.loads(form.getfirst('json'))
    except Exception, error:
      self.send_response(400)
      self.end_headers()
      self.wfile.write(str(error))
    else:
      try:
        if isinstance(json, list):
          map(self.ProcessCommand, json)
        else:
          self.ProcessCommand(json)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json)
      except Exception, error:
        self.send_response(400)
        self.end_headers()
        self.wfile.write(str(error))

  def ProcessCommand(self, command):
    if 'blender' in command:
      command['blender'] = getattr(utils, command['blender'])
    if 'envelope' in command:
      command['envelope'] = getattr(utils, command['envelope'])
    channel = self.server.box[command.pop('channel', 0)]
    action = getattr(channel, command.pop('action', 'fade').capitalize())
    action(**command)


def ApiServer(box, port=8000):
  server = BaseHTTPServer.HTTPServer(('0.0.0.0', port), ApiHandler)
  server.box = box
  server.serve_forever()
