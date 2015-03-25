#!/usr/bin/python
"""Lightbox utilities module

This module contains various utility functions to convert between RGB and LAB
color space, as well as envelope generators and color blenders.
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '2.3'

# Standard modules
import math
import operator
import random

# Colormath module
import colormath
from colormath import color_objects
from colormath.color_conversions import convert_color

def RandomColor(saturate=False):
  """Generates a random RGB color tuple.

  If `saturate` is set to True, it will be ensured that at least one of the
  three channels will have a value of under 50. This helps for LEDs that do not
  differentiate colors well on color outputs nearer the white.
  """
  color = map(random.randrange, [256] * 3)
  if saturate and min(color) > 50:
    color[random.randrange(3)] = 0
  return tuple(color)


# ##############################################################################
# Color blending functions
#
def ColorDiff(begin, target, factor=1):
  """Returns a color difference, multiplied by an effective factor.
  """
  return [operator.sub(*item) * factor for item in zip(target, begin)]


class Blenders(object):
  """A collection of layer blenders.

  These are collected in a class to simplify discovery.
  """
  @staticmethod
  def Darken(base, overlay, opacity):
    """Returns a tuple where the resulting lightness is the same or lower.

    The lightness is the L* component of Lab color.
    """
    if opacity == 0:
      return base
    base = LabColor(RgbToLab(base))
    l_overlay = RgbToLab(overlay)[0]
    if l_overlay < base.lab_l:
      base.lab_l += (l_overlay - base.lab_l) * opacity
    return LabToRgb(base.get_value_tuple())

  @staticmethod
  def Lighten(base, overlay, opacity):
    """Returns a tuple where the resulting lightness is the same or higher.

    The lightness is the L* component of Lab color.
    """
    if opacity == 0:
      return base
    base = LabColor(RgbToLab(base))
    l_overlay = RgbToLab(overlay)[0]
    if l_overlay > base.lab_l:
      base.lab_l += (l_overlay - base.lab_l) * opacity
    return LabToRgb(base.get_value_tuple())

  @staticmethod
  def RootSumSquare(base, overlay, opacity):
    """Returns the root of the base squared plus the difference squared.
    """
    if opacity == 0:
      return base
    diffs = ColorDiff(base, overlay, opacity)
    new_color = [sum(p ** 2 for p in pair) ** .5 for pair in zip(base, diffs)]
    # Ensure that no channel ever goes over value 255, this causes errors.
    return [min(255, chan) for chan in new_color]

  @staticmethod
  def RgbAverage(base, overlay, opacity):
    """Returns a tuple where each channel is the average of the given colors.
    """
    if opacity == 0:
      return base
    elif opacity == 1:
      return overlay
    return map(sum, zip(base, ColorDiff(base, overlay, opacity)))

  @staticmethod
  def LabAverage(base, overlay, opacity):
    """Returns a tuple where each channel is the average of the given colors.

    N.B. The average given is the RGB translation of the Lab colors averaged.
    """
    if opacity == 0:
      return base
    elif opacity == 1:
      return overlay
    base = RgbToLab(base)
    diffs = ColorDiff(base, RgbToLab(overlay), opacity)
    return LabToRgb(map(sum, zip(base, diffs)))


# ##############################################################################
# Envelope functions
#
class Envelopes(object):
  """A collection of transition envelopes.

  These are collected in a class to simplify discovery.
  """
  @staticmethod
  def Cosine(steps):
    """Yields `steps` number of multiplication factors following a cosine.

    The multiplication factors climb from 0 to 1 in the same fashion as a cosine
    function in the second half of the period.
    """
    for step in xrange(1, steps + 1):
      yield (math.cos(math.pi + math.pi * step / steps) + 1) / 2

  @staticmethod
  def Linear(steps):
    """Yields `steps` number of linearly increasing multiplication factors.

    The multiplication factor goes from 0 to 1 in the given number of `steps`.
    """
    for step in map(float, range(1, steps + 1)):
      yield step / steps


# ##############################################################################
# Gamma correction table creation
#
def GammaCorrectionList(gamma, in_bits=8, out_bits=8):
  """Returns a gamma-corrected list of level -> intensity

  The human eye reacts to changes in luminance in a non-linear fashion. To make
  each level change appear similar, we need to correct for this. A typical gamma
  factor that works for human eyes is 2.2.

  Arguments:
    @ gamma: float
      The gamma factor to calculate the list with. This would typically be 2.2.
    % in_bits: int ~~ 8
      The number of level bits, which determines the size of the output list
    % out_bits: int ~~ 8
      The number out intensity bits that are available on the hardware that
      the instructions are sent to.
  """
  scale_in = float(2 ** in_bits)
  scale_out = 2 ** out_bits
  gamma_func = lambda level: math.ceil(pow(level / scale_in, gamma) * scale_out)
  return map(int, map(gamma_func, range(2 ** in_bits)))


# ##############################################################################
# Color translation functions
#
def HexToRgb(hex_color):
  """Update the strip to the given hexadecimal color.

  N.B. This can be a short or long form color, with or without leading hash.
  """
  hex_color = hex_color.strip('#')
  if len(hex_color) == 3:
    colors = [n * 2 for n in hex_color]
  elif len(hex_color) == 6:
    colors = hex_color[:2], hex_color[2:4], hex_color[4:]
  else:
    raise ValueError('Hex color must be string of 3 or 6 hex chars.')
  return tuple(int(color, 16) for color in colors)


def LabColor(lab_color):
  """Returns the Lab color object with correct illuminant from a value tuple."""
  return color_objects.LabColor(*lab_color, illuminant='d65')


def LabToRgb(lab_color):
  """Returns a tuple of RGB colors for a given tuple of Lab components.
  """
  rgbcolor = convert_color(LabColor(lab_color), color_objects.sRGBColor)
  return rgbcolor.get_value_tuple()


def RgbToLab(rgb_color):
  """Returns a tuple of LabColor pairs for a given RGB color.

  The provided RGB color should either be a tuple (red, green, blue) or a hex
  string of 3 or 6 characters (with optional preceeding octothorpe)
  """
  if isinstance(rgb_color, basestring):
    rgb_color = HexToRgb(rgb_color)
  rgb_color = color_objects.sRGBColor(*rgb_color)
  return convert_color(rgb_color, color_objects.LabColor).get_value_tuple()
