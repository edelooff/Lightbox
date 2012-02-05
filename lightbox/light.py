#!/usr/bin/python
"""Lightbox library for JTAG's RGBController

This module contains the abstraction for the output lights, with various
methods that cause the lights to change in different manners.
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '1.2'

# Standard modules
import operator
import threading
import time

# Application modules
import utils

BLACK = 0, 0, 0


class Output(object):
  """Abstraction for an RGB output.

  Allows color changing using the associated controller.
  """
  def __init__(self, controller, output_id, **kwds):
    self.color = None
    self.channels = ChannelController()
    self.controller = controller
    self.output_id = output_id
    # Blender, output power adjuster and default color, optional arguments.
    self.Constant(kwds.get('color', BLACK))
    self.blender = kwds.get('blender', utils.RootSumSquare)
    self.outpower = kwds.get('outpower', utils.SoftQuadraticPower)
    self.ticker = OutputTicker(self._WriteNextColor)

  def __del__(self):
    self.StopTicker()

  # ############################################################################
  # Output color control
  #
  def Blink(self, color, count=1, steps=2, channel=0):
    """Blinks the output to the given `color` and back, `count` times."""
    current_channel_color = self.channels[channel].color or BLACK
    for _num in range(count):
      self.channels[channel].Append(Transition(color, steps))
      self.channels[channel].Append(Transition(current_channel_color, steps))

  def Constant(self, color, channel=0):
    """Instantly cuts the output over to the given RGB values."""
    self.channels[channel].Append(Transition(color, 1))

  def Fade(self, color, steps=40, channel=0):
    """Fades the output to the given `color` in `steps` steps."""
    self.channels[channel].Append(Transition(color, steps))

  # ############################################################################
  # Ticker control methods
  #
  def StartTicker(self):
    """(Re)starts the progression ticker."""
    self.ticker.running = True

  def StopTicker(self):
    """Temporarily stop the progression ticker."""
    self.ticker.running = False

  # ############################################################################
  # Private methods for acutal color control and transitions
  #
  def _WriteNextColor(self):
    begin_time = time.time()
    new_color = self._NextBlendedColor()
    new_color = map(int, map(self.outpower, new_color))
    if new_color != self.color:
      self.controller.SingleOutput(self.output_id, new_color)
      self.color = new_color
    self._WaitForTick(begin_time)

  def _NextBlendedColor(self):
    return self.blender(*next(self.channels))

  # ############################################################################
  # Timing control
  #
  def _WaitForTick(self, begin_time):
    """Sleeps for the remainder of the output's cycle time."""
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


class OutputTicker(threading.Thread):
  """Separate thread that continuously sends commands for the output color."""
  def __init__(self, function):
    super(OutputTicker, self).__init__()
    self.daemon = True
    self.function = function
    self.running = True
    self.start()

  def run(self):
    while self.running:
      self.function()


class Transition(object):
  """Class for creating a transition to a given color.

  To create an actual transition, call the FromColor method with a color to
  start the transition with.
  """
  def __init__(self, target_color, steps, envelope=None):
    """Initialized a Transition object.

    The target color is stored after conversion to CIELAB colorspace. The number
    of steps and the envelope function (which defasults to utils,CosineEnvelope)
    will be used to generate appropriate output streams.

    Arguments:
      @ target_color: 3-tuple of int
        Red, green and blue values that the transition should move to.
      @ steps: int
        The number of steps the transition should be completed in.
      % envelope: function ~~ utils.CosineEnvelope
        Envlope function to multiply the Lab difference with. This can be used
        to smoothen the transition.
    """
    if steps <= 0:
      raise ValueError('Steps argument must be at least 1.')
    self.envelope = envelope or utils.CosineEnvelope
    self.steps = steps
    self.target = utils.RgbToLab(target_color)

  def FromColor(self, start_color):
    """Generator for colortuples from the given color to the pre-set target.

    The starting color is first converted to CIELAB colorspace. Using the start
    and target colors, the difference is determined and the envelope function
    together with the number of steps will yield the requested number of steps
    to reach the preset target color.

    Arguments:
      @ from_rgb: 3-tuple of int
        Red, green and blue values to start the transition from.
    """
    begin_values = utils.RgbToLab(start_color or BLACK)
    lab_diff = [operator.sub(*item) for item in zip(self.target, begin_values)]
    for factor in self.envelope(self.steps):
      yield utils.LabToRgb(base + diff * factor for base, diff in
                           zip(begin_values, lab_diff))


class ColorChannel:
  """A single color channel that goes into a ChannelController to mix colors.

  An iterator that yields colors throughout transitions. When no transition is
  available, the last yielded color will be yielded indifinitely.

  N.B. Only Transition objects can be appended to this structure.
  """
  def __init__(self):
    """Initliazes a ColorChannel."""
    self.color = None
    self.current = None
    self.transitions = []

  def Append(self, transition):
    """Adds a new transition to be played after the current one.

    The new transition will be initiated with the then-current color.
    """
    if not isinstance(transition, Transition):
      raise TypeError('Can only append Transition objects.')
    self.transitions.append(transition)

  def Kill(self):
    """Resets the ColorChannel, immediately disabling output."""
    self.color = None
    self.current = None
    self.transitions = []

  def next(self):
    try:
      self.color = next(self.current)
      return self.color
    except (StopIteration, TypeError):
      if self.transitions:
        self.current = self.transitions.pop(0).FromColor(self.color)
        return next(self)
      return self.color


class ChannelController(object):
  def __init__(self, channels=3):
    self.channels = [ColorChannel() for _number in range(channels)]

  def __getitem__(self, index):
    return self.channels[index]

  def next(self):
    return filter(None, map(next, self.channels))
