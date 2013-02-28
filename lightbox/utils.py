#!/usr/bin/python
"""Lightbox library for JTAG's RGBController

This module contains various utility functions to convert between RGB and LAB
space, as well as envelope generators.
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '2.2'

# Standard modules
import math
import operator
import random

# Colormath module
from colormath import color_objects as colormath

# These define the blenders and envelope functions that may be used by the
# JSON API to control blending and transitions. If additional blenders and/or
# envelope functions are added, these tuples should be extended as well.
BLENDERS = 'RgbAverage', 'LabAverage', 'Darken', 'Lighten', 'RootSumSquare'
ENVELOPES = 'CosineEnvelope', 'LinearEnvelope'


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
  """Returns a color difference, multiplied by an effective factor."""
  return [operator.sub(*item) * factor for item in zip(target, begin)]


def Darken(base, overlay, opacity):
  """Returns a tuple where each channel is the darkest of the given colors."""
  if opacity == 0:
    return base
  diffs = ColorDiff(base, overlay, opacity)
  return [chan + min(0, diff) for chan, diff in zip(base, diffs)]


def Lighten(base, overlay, opacity):
  """Returns a tuple where each channel is the lightest of the given colors."""
  if opacity == 0:
    return base
  diffs = ColorDiff(base, overlay, opacity)
  return [chan + max(0, diff) for chan, diff in zip(base, diffs)]


def RootSumSquare(base, overlay, opacity):
  """Returns the root of the base squared plus the difference squared."""
  if opacity == 0:
    return base
  diffs = ColorDiff(base, overlay, opacity)
  new_color = [sum(p ** 2 for p in pair) ** .5 for pair in zip(base, diffs)]
  # Ensure that no channel ever goes over value 255, this causes errors.
  return [min(255, chan) for chan in new_color]


def RgbAverage(base, overlay, opacity):
  """Returns a tuple where each channel is the average of the given colors."""
  if opacity == 0:
    return base
  elif opacity == 1:
    return overlay
  return map(sum, zip(base, ColorDiff(base, overlay, opacity)))


def LabAverage(base, overlay, opacity):
  """Returns a tuple where each channel is the average of the given colors.

  N.B. The average given is the RGB translation of the Lab colors averaged."""
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
def CosineEnvelope(steps):
  """Yields `steps` number of multiplication factors following a cosine.

  The multiplication factors climb from 0 to 1 in the same fashion as a cosine
  function in the second half of the period.
  """
  for step in xrange(1, steps + 1):
    yield (math.cos(math.pi + math.pi * step / steps) + 1) / 2


def LinearEnvelope(steps):
  """Yields `steps` number of linearly increasing multiplication factors.

  The multiplication factor goes from 0 up to 1 in the given number of `steps`.
  """
  for step in map(float, range(1, steps + 1)):
    yield step / steps


# ##############################################################################
# Output power adjustment functions
#
def SoftQuadraticPower(power):
  """Adjusts the output power to the non-linearity of the LED outputs."""
  return pow(power, 1.8) / 99 + .15 * power


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
  """Wrapper for colormath.LabColor to get the correct illuminant."""
  return colormath.LabColor(*lab_color, illuminant='d65')


def LabToRgb(lab_color):
  """Returns a tuple of RGB colors for a given tuple of Lab values."""
  return LabColor(lab_color).convert_to('rgb').get_value_tuple()


def RgbToLab(rgb_color):
  """Returns a tuple of LabColor pairs for a given RGB color.

  The provided RGB color should either be a tuple (red, green, blue) or a hex
  string of 3 or 6 characters (with optional preceeding octothorpe)
  """
  if isinstance(rgb_color, basestring):
    rgb_color = HexToRgb(rgb_color)
  rgb_color = colormath.RGBColor(*rgb_color, illuminant='d65')
  return rgb_color.convert_to('lab').get_value_tuple()
