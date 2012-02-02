#!/usr/bin/python
"""Lightbox library for JTAG's RGBController

This module contains the basic controller interface and output management.
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '1.0'

# Standard modules
import random
import serial
import sys
import threading
import time

# Application modules
import light
import utils

# Controller and LED color init values
BLACK = 0, 0, 0
BLUE = 0, 0, 255
GREEN = 0, 255, 0
RED = 255, 0, 0
WHITE = 255, 255, 255
ALL_STRIPS = '#%d,%d,%d\r\n'


class ConnectionError(Exception):
  """A problem connecting to the USB serial light controller."""


class ColorController(list):
  """Controller interface for Danny's serial LED controller interface."""
  STRIP_CLASS = light.Strip
  HEARTBEAT = 'H\r\n'
  RESPONSE = 'R\r\n'

  def __init__(self, serial_conn, strips=5, color=BLACK):
    super(ColorController, self).__init__()
    self.lock = threading.Lock()
    self.serial = serial_conn
    self.frequency = self._DetectFrequency()
    self.heartbeat = Heartbeat(self.Heartbeat)
    self.last_strip_id = -1
    for _num in range(strips):
      self.Add(color)

  def __del__(self):
    self.heartbeat.perform = False

  def _DetectFrequency(self):
    """Returns the number of commands the controller handles in one second."""
    begin_time = time.time()
    frequency = 0
    while time.time() - begin_time < 1:
      self.Command(ALL_STRIPS % BLACK)
      frequency += 1
    print 'Controller frequency set to %dHz' % frequency
    return frequency

  def Command(self, command, verify=True):
    """Send the command to the serial device and wait for the confirmation."""
    with self.lock:
      try:
        self.serial.write(command)
      except serial.SerialException:
        raise ConnectionError('Could not send command.')
      if verify:
        response = self.serial.read(3)
        if response != self.RESPONSE:
          raise ConnectionError(
              'Incorrect acknowledgment: expected %r got: %r.' % (
              self.RESPONSE, response))

  def Heartbeat(self):
    """Sends a heartbeat signal to the controller without waiting for an ACK."""
    self.Command(self.HEARTBEAT, verify=False)

  # ############################################################################
  # LED Strip management
  #
  def Add(self, rgb_triplet=BLACK):
    """Adds a strip to the controller."""
    self.append(self.STRIP_CLASS(self, len(self), rgb_triplet))
    strip_frequency = float(self.frequency) / len(self)
    print 'Individual strip frequency now %.1fHz' % strip_frequency

  def Remove(self):
    """Removes a strip from the controller."""
    del_strip = self.pop()
    del_strip.InstantChange(BLACK)
    if del_strip.strip_id == self.last_strip_id:
      self.last_strip_id -= 1

  def Next(self):
    """Returns the next strip (based on the previously last used one."""
    strip_id = (self.last_strip_id + 1) % len(self)
    return self[strip_id]

  def Random(self):
    """Returns a semi-random strip and marks it as the most recently used one.

    N.B. It is guaranteed that the returned strip will *not* be the strip that
    was previously returned (the current `last_strip_id`).
    """
    options = range(len(self))
    options.pop(self.last_strip_id)
    return self[random.choice(options)]

  def __getitem__(self, index):
    """Returns the requested strip and stores the ID as `self.last_strip_id`."""
    strip_obj = super(ColorController, self).__getitem__(index)
    self.last_strip_id = index
    return strip_obj

  def append(self, item):
    """Overridden to only allow appending instances of self.strip_class."""
    if not isinstance(item, self.STRIP_CLASS):
      raise TypeError('Can only add proper strip objects to the controller.')
    super(ColorController, self).append(item)

  # ############################################################################
  # Color controls for all connected strips
  #
  def Fade(self, rgb_triplet, steps=40):
    """Fades all outputs to the given `rgb_triplet` in `steps` steps."""
    for strip_obj in self:
      strip_obj.Fade(rgb_triplet, steps=steps)

  def Instant(self, rgb_triplet):
    """Immediately changes all connected outputs to the given `rgb_triplet`."""
    self.Command(ALL_STRIPS % rgb_triplet)


class Heartbeat(threading.Thread):
  """Heartbeat keepalive thread to keep the LED controller happy."""
  def __init__(self, callback):
    super(Heartbeat, self).__init__(name=type(self).__name__)
    self.daemon = True
    self.callback = callback
    self.perform = True
    self.start()

  def run(self):
    """Main thread to send periodic keepalives."""
    time.sleep(5)
    while self.perform:
      try:
        self.callback()
        time.sleep(5)
      except ConnectionError:
        # Couldn't send a heartbeat, try again shortly to reanimate.
        time.sleep(1)


def Connect(device):
  """Returns a TreeColor instance connected to the given serial device name.

  We're waiting for a second after opening the device, this is because the
  LED controller needs some time before it behaves properly.
  """
  try:
    begin = time.time()
    conn = serial.Serial(device, 57600, timeout=1)
    conn.flushInput()
    print 'Buffer content length: %s' % len(conn.read())
    conn.timeout = .1
    for _attempt in range(5):
      conn.write(ALL_STRIPS % BLACK)
      if conn.read(3) == ColorController.RESPONSE:
        break
    else:
      raise ConnectionError('Device is not a JTAG RGBController.')
    print 'Initialization time: %.2f' % (time.time() - begin)
    print 'Connected to %s' % device
    return ColorController(conn)
  except serial.SerialException:
    raise ConnectionError('Could not open device %s.' % device)


def ConnectFirst():
  """Attempts to connect to any USB serial device."""
  for usb_index in range(5):
    try:
      return Connect('/dev/ttyUSB%d' % usb_index)
    except ConnectionError:
      pass
  raise ConnectionError('No device found :(')


def main():
  """Quick example demo that cycles colors for strip 0."""
  def Pause(tree):
    """Snaps the outputs to black and allows for a short wait between demos."""
    time.sleep(.2)
    tree.Instant(BLACK)
    time.sleep(1)

  print 'Demonstration program for the ColorController class and JTAG\'s box.\n'
  tree = ConnectFirst()
  print '\n1) Switching all outputs through red, green, blue ...'
  for color in [RED, BLACK, GREEN, BLACK, BLUE, BLACK] * 3:
    tree.Instant(color)
    time.sleep(.4)
  print '2) Fading all outputs through pure red, green, and blue ...'
  Pause(tree)
  for color in (RED, GREEN, BLUE, BLACK):
    tree.Fade(color)
    time.sleep(2.2)
  print '3) Double-blinking random outputs for 10 seconds ...'
  Pause(tree)
  for _count in range(30):
    tree.Random().Blink(utils.RandomTriplet(darken=True), 2)
    time.sleep(.35)
  print '4) Instantly changing colors on random outputs 1000x ...'
  Pause(tree)
  begin = time.time()
  for _count in range(1000):
    tree.Random().Instant(utils.RandomTriplet(darken=True))
    time.sleep(0.01)
  print '   1000 instant color changes took %.1fs.' % (time.time() - begin)
  print '5) Sequentialy fading to random colors at 500ms intervals ...'
  Pause(tree)
  print '\nThis is the last demonstration program, enjoy your blinky lights :-)'
  while True:
    tree.Next().Fade(utils.RandomTriplet(darken=True))
    time.sleep(.5)
    if not random.randrange(50):
      time.sleep(1)
      tree.Fade(utils.RandomTriplet(darken=True), 80)
      time.sleep(4)


if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print ''
    sys.exit()
