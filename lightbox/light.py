#!/usr/bin/python
"""Lightbox library for JTAG's RGBController

This module contains the abstraction for the output lights, with various
methods that cause the lights to change in different manners.
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '1.0'

# Standard modules
import itertools
import operator
import threading
import time

# Application modules
import utils

SINGLE_STRIP = '$%d,%d,%d,%d\r\n'


class Strip(object):
  """Abstraction for an RGB LED strip.

  Allows color changing using the associated controller.
  """
  def __init__(self, controller, strip_id, color):
    self.adjust = None
    self.strip_id = strip_id
    self.controller = controller
    self.color = color
    self.Instant(color)

  def __del__(self):
    """When removing a strip from the controller, stop current transitions."""
    self.StopTransition()

  # ############################################################################
  # Strip output color control
  #
  def Blink(self, rgb_triplet, count=1):
    """Blinks the output to the given `rgb_triplet` and back, `count` times."""
    blinks = []
    for _num in range(count):
      blinks.append(self._TransitionGenerator(self.color, rgb_triplet, 2))
      blinks.append(self._TransitionGenerator(rgb_triplet, self.color, 2))
    self._Transition(itertools.chain.from_iterable(blinks))

  def Fade(self, rgb_triplet, steps=40):
    """Fades the output to the given `rgb_triplet` in `steps` steps."""
    self._Transition(self._TransitionGenerator(self.color, rgb_triplet, steps))

  def Instant(self, rgb_triplet):
    """Instantly cuts the strip over to the given RGB values."""
    self._Transition([rgb_triplet])

  def StopTransition(self):
    """Stops any current color transition (fade or blink)."""
    if self.adjust:
      self.adjust.Stop()

  # ############################################################################
  # Private methods for acutal color control and transitions
  #
  def _ActualColorChange(self, rgb_triplet):
    """Changes the strip output to the given rgb_triplet.

    Additionally, the RGB triplet is stored on teh instance attribute `color`,
    and the appropiate time is spent sleeping to keep to the desired frequency.
    """
    begin_time = time.time()
    self.color = rgb_triplet
    red, green, blue = map(OutPowerAdjust, rgb_triplet)
    self.controller.Command(SINGLE_STRIP % (self.strip_id, red, green, blue))
    self._WaitForTick(begin_time)

  def _Transition(self, rgb_tuples):
    """Sets up a separate thread to control the actual transition from.

    This separate thread will cycle the strip through the colors provided by
    the rgb_tuples argument. After each step, a short pause is introduced to
    keep the strip's command frequency stable, independent of actual controller
    load.

    If a transition is currently running for this strip, that one will be
    interrupted before the new one is started.

    Arguments:
      @ rgb_tuples: iterable of 3-tuples
        A list or generator of RGB tuples that the StripAdjuster will cycle.
    """
    self.StopTransition()
    self.adjust = StripAdjuster(rgb_tuples, self._ActualColorChange)

  @staticmethod
  def _TransitionGenerator(from_rgb, to_rgb, steps, envelope=None):
    """Generator for tuples detailing the transition from one color to the next.

    The received `red`, `green`, and `blue` values are first converted to CIELAB
    colorspace, from where the difference path is calculated. The difference
    is then acted upon by a `envelope` function which returns the appropriate
    multiplication factors for the number of `steps` that the transition should
    take.

    Arguments:
      @ from_rgb: 3-tuple of int
        Red, green and blue values to start the transition from.
      @ to_rgb: 3-tuple of int
        Red, green and blue values to end the transition with.
      @ steps: int
        The number of steps the transition should be completed in.
      % envelope: function ~~ utils.CosineEnvelope
        Envlope function to multiply the Lab difference with. This can be used
        to smoothen the transition.
    """
    if envelope is None:
      envelope = utils.CosineEnvelope
    begin_values = utils.RgbToLab(from_rgb)
    final_values = utils.RgbToLab(to_rgb)
    lab_diff = [operator.sub(*item) for item in zip(final_values, begin_values)]
    for factor in envelope(steps):
      yield utils.LabToRgb(base + diff * factor for base, diff in
                           zip(begin_values, lab_diff))

  # ############################################################################
  # Timing control
  #
  def _WaitForTick(self, begin_time):
    """Sleeps for the remainder of the strip's cycle time."""
    remainder = begin_time + self.period - time.time()
    if remainder > 0:
      time.sleep(remainder)

  @property
  def period(self):
    """Returns the cyclic period time for the output as a float (seconds).

    This is based on the controller's frequency and the number of connected
    outputs. The period is 1 second divided by the frequency, multiplied by the
    connected outputs. This achieves a constant cycle time for each output,
    regardless of the number of outputs actually sending commands
    """
    return 1.0 / self.controller.frequency * len(self.controller)


class StripAdjuster(threading.Thread):
  """Separate thread to update the color of a strip with."""
  def __init__(self, steps, color_changer):
    super(StripAdjuster, self).__init__()
    self.daemon = True
    self.enabled = True
    self.steps = steps
    self.changer = color_changer
    self.start()

  def run(self):
    count = 0
    # starttime = time.time()
    for rgb_triplet in self.steps:
      if not self.enabled:
        print 'Interrupted after %d steps (%d remained)' % (
            count, len(list(self.steps)))
        return
      count += 1
      self.changer(rgb_triplet)
    # frequency = count / (time.time() - starttime)
    # print '[#%d] %d steps @ %.2fHz' % (self.strip.strip_id, count, frequency)

  def Stop(self):
    """Interrupts the StripAdjuster, allowing a new transition to start.

    If a running transition is not stopped, the output will start flickering
    between the values from the two separate transitions.
    """
    self.enabled = False


def OutPowerAdjust(power):
  """Adjusts the output power to the non-linearity of the LED strips."""
  return pow(power, 1.8) / 99 + .15 * power
