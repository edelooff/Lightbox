#!/usr/bin/python
"""Performs a lightbox demonstration run.

First, all ouputs cycle through their primary color channels, without any fading
or other smooth transitions. This is a simple step to verify the hardware works.

After that, the same primary colors are cycled again, but this time faded from
red to green to blue, demonstrating fading abilities.

Thirdly, random outputs blink random colors for a short while. This does not
serve any particular goal.

After that, a thousand random color cuts are performed. A strip is chosen at
random and its color output changed to another without delay. This does not
demonstrate the speed of the system though as there is still a configured 10ms
delay between color changes.

The last demonstration runs indefinitely and consist of random strips fading
to a new random color every half second. At a one in fifty chance, all strips on
the controller are changed to the same color, from where new individual
transitions continue to happen.
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '2.0'

# Standard modules
import random
import time

# Custom modules
from lightbox import controller
from lightbox import utils

# Controller and LED color init values
BLACK = 0, 0, 0
RED = 255, 0, 0
GREEN = 0, 255, 0
BLUE = 0, 0, 255
WHITE = 255, 255, 255


def Demo(controller_name):
  """Quick example demo that cycles colors for strip 0."""
  def Pause(box):
    """Snaps the outputs to black and allows for a short wait between demos."""
    time.sleep(.2)
    for output in box:
      output.Constant(color=BLACK)
    time.sleep(1)

  print 'Demonstration program for Lightbox.\n'
  print 'Initiating controller %r ...\n' % controller_name
  box = getattr(controller, controller_name).FirstDevice()

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


def main():
  """Processes commandline input to setup the demo."""
  import optparse
  import sys
  parser = optparse.OptionParser()
  parser.add_option('-c', '--controller', default='JTagController',
                    help='Controller class to instantiate.')
  options, _arguments = parser.parse_args()
  try:
    Demo(options.controller)
  except controller.ConnectionError:
    sys.exit('ABORT: Could not find a suitable device.')


if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print '\nEnd of demonstration.'
