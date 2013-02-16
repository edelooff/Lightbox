#!/usr/bin/python
"""Starts a demo on the strip, or sets up a JSON API for it."""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '2.0'

# Standard modules
import random
import sys
import time

# Custom modules
from lightbox import controller
from lightbox import json_api
from lightbox import utils

# Controller and LED color init values
BLACK = 0, 0, 0
BLUE = 0, 0, 255
GREEN = 0, 255, 0
RED = 255, 0, 0
WHITE = 255, 255, 255


def Demo(box):
  """Quick example demo that cycles colors for strip 0."""
  def Pause(box):
    """Snaps the outputs to black and allows for a short wait between demos."""
    time.sleep(.2)
    for output in box:
      output.Constant(color=BLACK)
    time.sleep(1)

  print 'Demonstration program for the ColorController class and JTAG\'s box.\n'
  print '\n1) Switching all outputs through red, green, blue ...'
  for color in [RED, BLACK, GREEN, BLACK, BLUE, BLACK] * 3:
    box.SetAll(color)
    time.sleep(.4)
  print '2) Fading all outputs through pure red, green, and blue ...'
  Pause(box)
  for color in (RED, GREEN, BLUE, BLACK):
    for output in box:
      output.Fade(color=color, opacity=1, steps=40)
    time.sleep(2.2)
  print '3) Double-blinking random outputs for 10 seconds ...'
  Pause(box)
  for _count in range(30):
    box.Random().Blink(color=utils.RandomColor(saturate=True), count=2)
    time.sleep(.35)
  print '4) Instantly changing colors on random outputs 1000x ...'
  Pause(box)
  begin = time.time()
  for _count in range(1000):
    box.Random().Constant(color=utils.RandomColor(saturate=True))
    time.sleep(0.01)
  print '   1000 instant color changes took %.1fs.' % (time.time() - begin)
  print '5) Sequentialy fading to random colors at 500ms intervals ...'
  Pause(box)
  print '\nThis is the last demonstration program, enjoy your blinky lights :-)'
  while True:
    box.Next().Fade(color=utils.RandomColor(saturate=True), steps=40)
    time.sleep(.5)
    if not random.randrange(50):
      time.sleep(1)
      color = utils.RandomColor(saturate=True)
      for output in box:
        output.Fade(color=color, opacity=1, steps=80)
      time.sleep(4)


if __name__ == '__main__':
  USAGE_ERROR = '%%s:\n  Usage: %s [ demo | api ]' % sys.argv[0]
  if len(sys.argv) < 2:
    sys.exit(USAGE_ERROR % 'No action provided')
  try:
    if sys.argv[1] == 'demo':
      Demo(controller.JTagController.ConnectFirst())
    elif sys.argv[1] == 'api':
      json_api.ApiServer(controller.JTagController.ConnectFirst())
    else:
      sys.exit(USAGE_ERROR % 'Bad command')
  except KeyboardInterrupt:
    print '\nBye :-)'
