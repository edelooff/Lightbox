#!/usr/bin/python
"""Layer mixing demonstration of Lightbox"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '2.0'

# Standard modules
import time

# Custom modules
from lightbox import controller

# Named colors
RED = 255, 0, 0
ORANGE = 25, 128, 0
YELLOW = 255, 255, 0
GREEN = 0, 255, 0
PURPLE = 255, 0, 255
BLUE = 0, 0, 255
WHITE = 255, 255, 255


def Statics(box):
  colors = RED, GREEN, BLUE, YELLOW, PURPLE
  for output, color in zip(box, colors):
    output.Constant(color=color, opacity=1)
    time.sleep(.5)


def Primary(box):
  for output in box:
    output.AddLayer()
    # Set initial colors
    output.Constant(layer=0, color=(20, 0, 0), opacity=1)
    output.Constant(layer=1, color=(0, 20, 0), opacity=.4)
    output.Constant(layer=2, color=(0, 0, 20), opacity=.4)
    # Start back and forth fades
    output.Blink(layer=0, color=RED, steps=300, count=2)
    output.Blink(layer=1, color=GREEN, steps=150, count=6)
    output.Blink(layer=2, color=BLUE, steps=100, count=9)
  try:
    while True:
      raw_input('[enter] for quick flash, Control-C to continue ...')
      for output in box:
        output.Blink(layer=3, color=WHITE, opacity=1, steps=1)
      time.sleep(.15)
  except KeyboardInterrupt:
    for output in box:
      output.DeleteLayer()
    print '\nTime for the next demo!'


def Secondary(box):
  for output in box:
    for layer in output:
      layer.Kill()
  # Odd outputs get mad blinkies
  for output in box[::2]:
    # red <-> blue fades happening in channel 1
    output.Fade(color=RED, steps=100, opacity=1)
    output.Blink(color=BLUE, steps=100, count=2)
    # orange <-> green fades happening in channel 2
    output.Constant(layer=1, color=ORANGE, steps=1)
    output.Blink(layer=1, color=GREEN, steps=200, opacity=.5)
    # Blinks for channel 3
    output[2].color = WHITE
    output.Blink(layer=2, count=30, opacity=.5, steps=4)
  # Even outputs get blow fades
  for output in box[1::2]:
    # red <-> blue fades happening in channel 1
    output.Fade(color=BLUE, steps=50, opacity=1)
    output.Blink(color=RED, steps=100, count=2)
  try:
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    print 'Bye!'


if __name__ == '__main__':
  BOX = controller.JTagController.ConnectFirst()
  Statics(BOX)
  Primary(BOX)
  Secondary(BOX)
