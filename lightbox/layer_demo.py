#!/usr/bin/python

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
    for _i in range(3):
      output.Constant(layer=0, color=(20, 0, 0), opacity=1)
      output.Fade(layer=0, color=(255, 0, 0), steps=300)
      output.Fade(layer=0, color=(20, 0, 0), steps=300)
    for _i in range(6):
      output.Constant(layer=1, color=(0, 20, 0), opacity=.4)
      output.Fade(layer=1, color=(0, 255, 0), steps=150)
      output.Fade(layer=1, color=(0, 20, 0), steps=150)
    for _i in range(9):
      output.Constant(layer=2, color=(0, 0, 20), opacity=.4)
      output.Fade(layer=2, color=(0, 0, 255), steps=100)
      output.Fade(layer=2, color=(0, 0, 20), steps=100)
  try:
    while True:
      raw_input('[enter] for quick flash, Control-C to continue ...')
      for output in controller:
        output.Blink(layer=3, color=(255, 255, 255), opacity=1, steps=1)
        time.sleep(.1)
  except KeyboardInterrupt:
    for output in controller:
      output.DeleteLayer()
    print '\nTime for the next demo!'


def Secondary(controller):
  for output in controller[::2]:
    # red <-> blue fades happening in channel 1
    output.Fade(0, color=lightbox.RED, steps=100, opacity=1)
    output.Fade(0, color=lightbox.BLUE, steps=100)
    output.Fade(0, color=lightbox.RED, steps=100)
    output.Fade(0, color=lightbox.BLUE, steps=100)
    # orange <-> green fades happening in channel 2
    output.Fade(layer=1, color=(255, 128, 0), steps=1)
    output.Fade(layer=1, color=lightbox.GREEN, steps=200, opacity=.5)
    output.Fade(layer=1, color=(255, 128, 0), steps=200, opacity=.5)
    # Blinks for channel 3
    output[2].color = 255, 255, 255
    output.Blink(layer=2, count=30, opacity=.5, steps=4)

  for output in controller[1::2]:
    # red <-> blue fades happening in channel 1
    output.Fade(color=lightbox.BLUE, steps=50, opacity=1)
    output.Fade(color=lightbox.RED, steps=100)
    output.Fade(color=lightbox.BLUE, steps=100)
    output.Fade(color=lightbox.RED, steps=100)
    output.Fade(color=lightbox.BLUE, steps=100)
  try:
    time.sleep(1)
  except KeyboardInterrupt:
    print 'Bye!'


if __name__ == '__main__':
  controller = lightbox.JTagController.ConnectFirst()
  Statics(controller)
  Primary(controller)
  Secondary(controller)
