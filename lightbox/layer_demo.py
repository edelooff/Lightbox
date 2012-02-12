#!/usr/bin/python
"""Layer mixing demonstration of Lightbox
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '0.3'

# Standard modules
import time

# Custom modules
from frack.projects import lightbox
from frack.projects.lightbox import light
from frack.projects.lightbox import utils


def Statics(controller):
  colors = (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)
  for output, color in zip(controller, colors):
    output.Constant(color=color, opacity=1)
    time.sleep(.5)


def Primary(controller):
  for output in controller:
    output.AddLayer()
    # Set initial colors
    output.Constant(layer=0, color=(20, 0, 0), opacity=1)
    output.Constant(layer=1, color=(0, 20, 0), opacity=.4)
    output.Constant(layer=2, color=(0, 0, 20), opacity=.4)
    # Start back and forth fades
    output.Blink(layer=0, color=(255, 0, 0), steps=300, count=2)
    output.Blink(layer=1, color=(0, 255, 0), steps=150, count=6)
    output.Blink(layer=2, color=(0, 0, 255), steps=100, count=9)
  try:
    while True:
      raw_input('[enter] for quick flash, Control-C to continue ...')
      for output in controller:
        output.Blink(layer=3, color=(255, 255, 255), opacity=1, steps=1)
      time.sleep(.15)
  except KeyboardInterrupt:
    for output in controller:
      output.DeleteLayer()
    print '\nTime for the next demo!'


def Secondary(controller):
  for output in controller:
    for layer in output:
      layer.Kill()
  # Odd outputs get mad blinkies
  for output in controller[::2]:
    # red <-> blue fades happening in channel 1
    output.Fade(color=lightbox.RED, steps=100, opacity=1)
    output.Blink(color=lightbox.BLUE, steps=100, count=2)
    # orange <-> green fades happening in channel 2
    output.Constant(layer=1, color=(255, 128, 0), steps=1)
    output.Blink(layer=1, color=lightbox.GREEN, steps=200, opacity=.5)
    # Blinks for channel 3
    output[2].color = 255, 255, 255
    output.Blink(layer=2, count=30, opacity=.5, steps=4)
  # Even outputs get blow fades
  for output in controller[1::2]:
    # red <-> blue fades happening in channel 1
    output.Fade(color=lightbox.BLUE, steps=50, opacity=1)
    output.Blink(color=lightbox.RED, steps=100, count=2)
  try:
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    print 'Bye!'


if __name__ == '__main__':
  controller = lightbox.JTagController.ConnectFirst()
  Statics(controller)
  Primary(controller)
  Secondary(controller)
