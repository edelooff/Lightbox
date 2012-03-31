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
      self.wfile.write(str(error))
    else:
      try:
        if isinstance(json, list):
          for command in json:
            channel = self.server.box[command.pop('channel', 0)]
            action_name = command.pop('action', 'fade').capitalize()
            action = getattr(channel, action_name)
            action(**command)
        elif isinstance(json, dict):
          channel = self.server.box[json.pop('channel', 0)]
          action = getattr(channel, json.pop('action', 'fade').capitalize())
          action(**json)
        else:
          self.send_response(400)
          self.wfile.write('Request should be an object or list of objects.')
      except Exception, error:
        self.send_response(400)
        self.wfile.write(str(error))


def ApiServer(box, port=8000):
  server = BaseHTTPServer.HTTPServer(('localhost', port), ApiHandler)
  server.box = box
  server.serve_forever()
