#!/usr/bin/python
"""Lightbox library for JTAG's RGBController

This module contains the abstraction for the output lights, with various
methods that cause the lights to change in different manners.
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '1.3'

# Standard modules
import threading
import time

# Application modules
import utils


class Output(object):
  """Abstraction for an RGB output.

  Allows color changing using the associated controller.
  """
  def __init__(self, controller, output_id, **kwds):
    self.color = None
    self.mixer = LayerMixer(layers=kwds.get('layers', 3))
    self.controller = controller
    self.output_id = output_id
    # Blender, output power adjuster and default color, optional arguments.
    self.outpower = kwds.get('outpower', utils.SoftQuadraticPower)
    self.ticker = OutputTicker(self._WriteNextColor)

  def __del__(self):
    self.StopTicker()

  # ############################################################################
  # Output color control
  #
  def Blink(self, layer=0, count=1, **options):
    """Blinks the output to the given `color` and back, `count` times."""
    trans_back = options.copy()
    trans_back['color'] = self.mixer[layer].color
    trans_back['opacity'] = self.mixer[layer].opacity
    for _num in range(count):
      self.mixer[layer].Append(Transition(**options))
      self.mixer[layer].Append(Transition(**trans_back))

  def Constant(self, layer=0, **options):
    """Instantly cuts the output over to the given RGB values."""
    options['steps'] = 1
    self.mixer[layer].Append(Transition(**options))

  def Fade(self, layer=0, **options):
    """Fades the output to the given `color` in `steps` steps."""
    self.mixer[layer].Append(Transition(**options))

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
    new_color = next(self.mixer)
    new_color = map(int, map(self.outpower, new_color))
    if new_color != self.color:
      self.controller.SingleOutput(self.output_id, new_color)
      self.color = new_color
    self._WaitForTick(begin_time)

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
  def __init__(self, **options):
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
    self.steps = options.get('steps', 1)
    if self.steps <= 0:
      raise ValueError('Steps argument must be at least 1.')
    if 'color' in options:
      self.color = utils.RgbToLab(options['color'])
    else:
      self.color = None
    self.blender = options.get('blender', utils.LabAverage)
    self.envelope = options.get('envelope', utils.CosineEnvelope)
    self.opacity = options.get('opacity')

  def FromColor(self, color, opacity):
    """Generator for colortuples from the given color to the pre-set target.

    The starting color is first converted to CIELAB colorspace. Using the start
    and target colors, the difference is determined and the envelope function
    together with the number of steps will yield the requested number of steps
    to reach the preset target color.

    Arguments:
      @ color: 3-tuple of int
        Red, green and blue values to start the transition from.
      @ opacity: float
        Opacity value that the transition should start with.
    """
    lab_begin, lab_diff = self._LabDiff(color)
    if self.opacity is None:
      opacity_diff = 0
    else:
      opacity_diff = self.opacity - opacity
    for factor in self.envelope(self.steps):
      new_color = utils.LabToRgb(base + diff * factor for base, diff
                                 in zip(lab_begin, lab_diff))
      new_opacity = opacity + opacity_diff * factor
      yield new_color, new_opacity

  def _LabDiff(self, color):
    begin = utils.RgbToLab(color)
    return begin, utils.ColorDiff(begin, self.color or begin)


class Layer(object):
  """A single color layer that goes into a LayerMixer to mix colors.

  An iterator that yields colors throughout transitions. When no transition is
  available, the last yielded color will be yielded indifinitely.

  N.B. Only Transition objects can be appended to this structure.
  """
  def __init__(self, color=(0, 0, 0), opacity=0, blender=utils.LabAverage):
    """Initliazes a Layer."""
    # Layer management
    self.blender = blender
    self.color = color
    self.opacity = opacity
    # Transition management
    self.current_transition = None
    self.transitions = []

  def Append(self, transition):
    """Adds a new transition to be played after the current one.

    The new transition will be initiated with the then-current color.
    """
    if not isinstance(transition, Transition):
      raise TypeError('Can only append Transition objects.')
    self.transitions.append(transition)

  def Kill(self):
    """Resets the Layer, immediately disabling output."""
    self.color = 0, 0, 0
    self.opacity = 0
    self.current_transition = None
    self.transitions = []

  def NextBlendedColor(self, base):
    overlay, opacity = next(self)
    return self.blender(base, overlay, opacity)

  def next(self):
    try:
      self.color, self.opacity = next(self.current_transition)
      return self.color, self.opacity
    except (StopIteration, TypeError):
      if self.transitions:
        transition = self.transitions.pop(0)
        self.blender = transition.blender
        self.current_transition = transition.FromColor(self.color, self.opacity)
        return next(self)
      return self.color, self.opacity


class LayerMixer(object):
  def __init__(self, layers=4):
    self.layers = [Layer() for _number in range(layers)]

  def __getitem__(self, index):
    return self.layers[index]

  def next(self):
    color = 0, 0, 0
    for layer in self.layers:
      color = layer.NextBlendedColor(color)
    return color
