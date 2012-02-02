#!/usr/bin/python
"""Lightbox library for JTAG's RGBController

This module contains various utility functions to convert between RGB and LAB
space, as well as envelope generators.
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '1.0'

# Standard modules
import math
import random

# Colormath module
from colormath import color_objects as colormath


def RandomTriplet(darken=False):
  """Generates a random RGB color triplet.

  If `darken` is set to True, it will be ensured that at least one of the three
  channels will have a value of under 50. This helps for LEDs that do not
  differentiate colors well on color outputs nearer the white.
  """
  triplet = map(random.randrange, [256] * 3)
  if darken and min(triplet) > 50:
    triplet[random.randrange(3)] = 0
  return tuple(triplet)


# ##############################################################################
# Color blending functions
#
def Darken(*colors):
  """Returns a tuple where each channel is the darkest of the given colors."""
  return tuple(map(min, zip(*colors)))


def Lighten(*colors):
  """Returns a tuple where each channel is the lightest of the given colors."""
  return tuple(map(max, zip(*colors)))


def RgbAverage(*colors):
  """Returns a tuple where each channel is the average of the given colors."""
  return tuple(sum(channels) / len(channels) for channels in zip(*colors))


def LabAverage(*colors):
  """Returns a tuple where each channel is the darkest of the given colors.

  N.B. The average given is the RGB translation of the Lab colors averaged."""
  colors = map(RgbToLab, colors)
  return LabToRgb(sum(channels) / len(channels) for channels in zip(*colors))


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
# Color translation functions
#
def HexToRgb(hex_color):
  """Update the strip to the given hexadecimal color.

  N.B. This can be a short or long form triplet, with or without leading hash.
  """
  hex_color = hex_color.strip('#')
  if len(hex_color) == 3:
    colors = [n * 2 for n in hex_color]
  elif len(hex_color) == 6:
    colors = hex_color[:2], hex_color[2:4], hex_color[4:]
  else:
    raise ValueError('Hex color must be string of 3 or 6 hex chars.')
  return tuple(int(color, 16) for color in colors)


def LabColor(lab_triplet):
  """Wrapper for colormath.LabColor to get the correct illuminant."""
  return colormath.LabColor(*lab_triplet, illuminant='d65')


def LabToRgb(lab_triplet):
  """Returns a tuple of RGB colors for a given triplet of Lab values."""
  return LabColor(lab_triplet).convert_to('rgb').get_value_tuple()


def RgbToLab(rgb_triplet):
  """Returns a tuple of LabColor pairs for a given RGB triplet."""
  rgb_color = colormath.RGBColor(*rgb_triplet, illuminant='d65')
  return rgb_color.convert_to('lab').get_value_tuple()
