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
  """Statically displays a set of colors on five outputs."""
  colors = RED, YELLOW, GREEN, BLUE, PURPLE
  for output, color in zip(box, colors):
    output.Constant(color=color, opacity=1)


def Primary(box):
  """The first demo, back and forth fades and user-controlled flashes."""
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
  """Continuous final demonstration."""
  for output in box:
    for layer in output:
      layer.Kill()
  while True:
    # Odd outputs get fast blinking
    for output in box[::2]:
      # red <-> blue fades happening in channel 1
      output.Fade(color=RED, steps=100, opacity=1)
      output.Blink(color=BLUE, steps=100, count=2)
      # orange <-> green fades happening in channel 2
      output.Constant(layer=1, color=ORANGE, steps=1)
      output.Blink(layer=1, color=GREEN, steps=200, opacity=.5)
      # Blinks for channel 3
      output[2].color = WHITE
      output.Blink(layer=2, count=30, opacity=.5, steps=7)
    # Even outputs get slow fades
    for output in box[1::2]:
      # red <-> blue fades happening in channel 1
      output.Fade(color=BLUE, steps=50, opacity=1)
      output.Blink(color=RED, steps=100, count=2)
    time.sleep(1)


def LayerDemo(controller_name, outputs):
  """Demonstrates layer blending operation of Lightbox."""
  print 'Demonstrating layer blending in Lightbox.\n'
  print 'Initiating controller %r ...\n' % controller_name
  box = getattr(controller, controller_name).FirstDevice(outputs=outputs)
  Statics(box)
  time.sleep(.5)
  Primary(box)
  Secondary(box)


def main():
  """Processes commandline input to setup the demo."""
  import optparse
  import sys
  parser = optparse.OptionParser()
  parser.add_option('-c', '--controller', default='NewController',
                    help='Controller class to instantiate.')
  parser.add_option('-o', '--outputs', type='int', default=5,
                    help='Number of outputs to use on the hardware.')
  options, _arguments = parser.parse_args()
  try:
    LayerDemo(options.controller, options.outputs)
  except controller.ConnectionError:
    sys.exit('ABORT: Could not find a suitable device.')
  except KeyboardInterrupt:
    print '\nEnd of demonstration.'


if __name__ == '__main__':
  main()
