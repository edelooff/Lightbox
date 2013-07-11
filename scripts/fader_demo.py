#!/usr/bin/python
"""Slowly fades all outputs between black and white continuously.

This is a simple script to test whether the non-linear response to luminance
 by the human eye is properly corrected for.
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '1.0'

# Standard modules
import time

# Custom modules
from lightbox import controller
from lightbox import utils


def Demo(controller_name, outputs):
  """Sweeping from low to high brightness and back, continuously."""
  print 'Initiating controller %r ...\n' % controller_name
  box = getattr(controller, controller_name).FirstDevice(outputs=outputs)
  print '\nFade to white and back.'
  FadeOutputs(box, '#fff')
  FadeOutputs(box, '#000')
  print 'Fade to a random color and back to black, ad nauseum.'
  while True:
    FadeOutputs(box, utils.RandomColor())
    FadeOutputs(box, '#000')


def FadeOutputs(box, color, steps=50):
  """Fades all outputs to the given color and waits for it to complete."""
  for output in box:
    output.Fade(color=color, steps=steps)
  time.sleep(steps / (float(box.frequency) / len(box)))


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
    Demo(options.controller, options.outputs)
  except controller.ConnectionError:
    sys.exit('ABORT: Could not find a suitable device.')


if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print '\nEnd of demonstration.'
