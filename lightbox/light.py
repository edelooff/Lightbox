#!/usr/bin/python
"""Lightbox library for JTAG's RGBController

This module contains the abstraction for the output lights, with various
methods that cause the lights to change in different manners.
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '2.0'

# Standard modules
import collections

# Application modules
import utils


class ActionsMixIn(object):
  """Provides the common actions for Output classes."""
  def Blink(self, layer=0, count=1, **options):
    """Blinks the output to the given `color` and back, `count` times."""
    options['withreverse'] = True
    for _num in range(count):
      self[layer].Append(Transition(**options))

  def Constant(self, layer=0, **options):
    """Instantly cuts the output over to the given RGB values."""
    options['steps'] = 1
    self[layer].Append(Transition(**options))

  def Fade(self, layer=0, **options):
    """Fades the output to the given `color` in `steps` steps."""
    self[layer].Append(Transition(**options))


class Output(ActionsMixIn):
  """Abstraction for an RGB output.

  Allows color changing using the associated controller.
  """
  def __init__(self, layers=3):
    super(Output, self).__init__()
    self.color = 0, 0, 0
    self.layers = [Layer() for _number in range(max(1, layers))]

  # ############################################################################
  # Actual color changing/writing and layer management
  #
  def __getitem__(self, index):
    """Retrieves a layer by index."""
    return self.layers[index]

  def __iter__(self):
    """Returns an iterator for the Layer objects in the output."""
    return iter(self.layers)

  def next(self):
    """Returns the combined next color for the output."""
    color, _opacity = next(self[0])
    for layer in self[1:]:
      color = layer.NextBlendedColor(color)
    return tuple(map(int, color))

  def AddLayer(self):
    """Adds an additional layer to this output."""
    self.layers.append(Layer())

  def DeleteLayer(self, index=None):
    """Deletes the topmost layer from the output, or layer at `index` if given.

    If an attempt is made to remove the last layer, ValueError is raised.
    """
    if len(self.layers) == 1:
      raise ValueError('May not remove the last layer.')
    index = -1 if index is None else index
    self.layers.pop(index)

  def NewColor(self):
    """Calculates and returns the new color tuple for this output.

    If the new color is the same as the current color, None is returned instead
    of an RGB color tuple.
    """
    new_color = next(self)
    if new_color != self.color:
      self.color = new_color
      return new_color


class Layer(object):
  """A single color layer that goes into a LayerMixer to mix colors.

  An iterator that yields colors throughout transitions. When no transition is
  available, the last yielded color will be yielded indifinitely.

  N.B. Only Transition objects can be appended to this structure.
  """
  def __init__(self, **opts):
    """Initliazes a Layer."""
    # Layer management
    self.blender = opts.get('blender', utils.Blenders.LabAverage)
    self.color = opts.get('color', (0, 0, 0))
    self.opacity = opts.get('opacity', 0)
    # Transition management
    self.envelope = opts.get('envelope', utils.Envelopes.Cosine)
    self.queue = collections.deque()
    self.transition = None

  def Append(self, transition):
    """Adds a new transition to be played after the current one.

    The new transition will be initiated with the then-current color.
    """
    if not isinstance(transition, Transition):
      raise TypeError('Can only append Transition objects.')
    if transition.options.get('queue', True):
      self.queue.append(transition)
    else:
      self.NewTransition(transition)
      self.queue.clear()

  def Kill(self):
    """Resets the Layer, immediately disabling output."""
    self.color = 0, 0, 0
    self.opacity = 0
    self.queue = collections.deque()
    self.transition = None

  def NewTransition(self, transition):
    """Installs the new transition and blender."""
    self.blender = transition.blender or self.blender
    self.transition = transition.Start(self.color, self.opacity, self.envelope)

  def NextBlendedColor(self, base):
    """Returns the next blended color for this Layer.

    The layer's own next color is blended with the given base color,
    proportional to the layer's opacity.
    """
    overlay, opacity = next(self)
    return self.blender(base, overlay, opacity)

  def next(self):
    """Steps through the current transition and returns color and opacity.

    If there are no transitions queued up, this will return the current color
    and opacity instead.
    """
    try:
      self.color, self.opacity = next(self.transition)
      return self.color, self.opacity
    except (StopIteration, TypeError):
      if not self.queue:
        # No new transitions are queued up; return the current values
        return self.color, self.opacity
      # Load a new transition and set transition information
      self.NewTransition(self.queue.popleft())
      return next(self)


class Transition(object):
  """Class for creating a transition to a given color.

  To create an actual transition, call the FromColor method with a color to
  start the transition with.
  """
  def __init__(self, **opts):
    """Initialized a Transition object.

    The target color is stored after conversion to CIELAB colorspace. The number
    of steps and the envelope function (which defasults to utils,CosineEnvelope)
    will be used to generate appropriate output streams.

    Arguments:
      @ steps: int
        The number of steps the transition should be completed in.
      % color: 3-tuple of int
        Red, green and blue values that the transition should move to. If no
        color is given, it will remain as it was at the start of the transition.
      % opacity: float
        Opacity value that the transition should move towards. If no opacity is
        given, it will remain as it was at the start of the transition.
      % blender: function
        The color blender that should be used to blend the color output from
        this transition. If not given, the blender in use at time of the start
        of this transition is used.
      % envelope: function
        Envlope to apply to the color transition. This is used to provide
        different smoothings to the transition. If not given, the envelope
        function in use at time of the start of this transition is used.
    """
    self.steps = int(opts.get('steps', 1))
    if self.steps <= 0:
      raise ValueError('Steps argument must be at least 1.')
    self.color = utils.RgbToLab(opts.get('color')) if 'color' in opts else None
    self.blender = opts.get('blender', None)
    self.options = opts

  def Start(self, color, opacity, envelope):
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
      @ envelope: function
        Envelope function that was used for the previous transition. If there
        is no explicit envelope set for this transition, the previous one will
        be used.
    """
    lab_begin, lab_diff = self._LabDiff(color)
    opacity_diff = self.options.get('opacity', opacity) - opacity
    for factor in self.options.get('envelope', envelope)(self.steps):
      yield (utils.LabToRgb(base + diff * factor for base, diff
                            in zip(lab_begin, lab_diff)),
             opacity + opacity_diff * factor)
    if self.options.get('withreverse', False):
      for factor in self.options.get('envelope', envelope)(self.steps):
        yield (utils.LabToRgb(base + diff * (1 - factor) for base, diff
                              in zip(lab_begin, lab_diff)),
               opacity + opacity_diff * (1 - factor))

  def _LabDiff(self, color):
    begin = utils.RgbToLab(color)
    return begin, utils.ColorDiff(begin, self.color or begin)
