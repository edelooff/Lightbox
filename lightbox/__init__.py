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


class ConnectionError(Exception):
  """A problem connecting to the USB serial light controller."""


class Heartbeat(threading.Thread):
  """Heartbeat keepalive thread to keep the LED controller happy."""
  def __init__(self, callback, delay=5, fail_delay=1):
    super(Heartbeat, self).__init__(name=type(self).__name__)
    self.daemon = True
    # Heartbeat controls:
    self.beat = True
    self.callback = callback
    self.delay = delay
    self.fail_delay = fail_delay
    self.start()

  def run(self):
    """Main thread to send periodic keepalives."""
    time.sleep(self.delay)
    while self.beat:
      try:
        self.callback()
        print 'whop whop'
        time.sleep(self.delay)
      except ConnectionError:
        time.sleep(self.fail_delay)


class ColorController(list):
  """Controller interface for Danny's serial LED controller interface."""
  OUTPUT_CLASS = light.Output

  def __init__(self, connection, outputs=5, init_color=BLACK):
    super(ColorController, self).__init__()
    self.lock = threading.Lock()
    self.serial = connection
    self.frequency = self._DetectFrequency()
    self.heartbeat = Heartbeat(self._Heartbeat)
    self.last_output_id = -1
    for _num in range(outputs):
      self.Add(init_color)

  def __del__(self):
    """Disables heartbeat upon shutdown."""
    self.heartbeat.beat = False

  @classmethod
  def Connect(cls, device):
    raise NotImplementedError

  @classmethod
  def ConnectFirst(cls):
    """Attempts to connect to first 10 USB serial devices."""
    for usb_index in range(10):
      try:
        return cls.Connect('/dev/ttyUSB%d' % usb_index)
      except ConnectionError:
        pass
    raise ConnectionError('No suitable found :(')

  def Command(self, command, verify=True):
    """Send the command to the serial device and wait for the confirmation."""
    with self.lock:
      try:
        self.serial.write(command)
      except serial.SerialException:
        raise ConnectionError('Could not send command.')
      verify and self._Verify()

  # ############################################################################
  # Output add/removal
  #
  def Add(self, rgb_triplet=BLACK):
    """Adds an output to the controller."""
    self.append(self.OUTPUT_CLASS(self, len(self), rgb_triplet))
    output_frequency = float(self.frequency) / len(self)
    print 'Individual output frequency now %.1fHz' % output_frequency

  def Remove(self):
    """Removes an output from the controller."""
    del_output = self.pop()
    del_output.InstantChange(BLACK)
    if del_output.output_id == self.last_output_id:
      self.last_output_id -= 1

  def __getitem__(self, index):
    """Returns the requested output and writes it to `self.last_output_id`."""
    output = super(ColorController, self).__getitem__(index)
    self.last_output_id = index
    return output

  def append(self, item):
    """Overridden to only allow appending instances of self.OUTPUT_CLASS."""
    if not isinstance(item, self.OUTPUT_CLASS):
      raise TypeError('Can only add proper output objects to the controller.')
    super(ColorController, self).append(item)


  # ############################################################################
  # Output cycling
  #
  def Next(self):
    """Returns the next output (based on the previously last used one."""
    output_id = (self.last_output_id + 1) % len(self)
    return self[output_id]

  def Random(self):
    """Returns a semi-random output and marks it as the most recently used one.

    N.B. It is guaranteed that the returned output will *not* be the output that
    was previously returned (the current `last_output_id`).
    """
    options = range(len(self))
    options.pop(self.last_output_id)
    return self[random.choice(options)]

  # ############################################################################
  # Color controls for all connected outputs
  #
  def Fade(self, rgb_triplet, steps=40):
    """Fades all outputs to the given `rgb_triplet` in `steps` steps."""
    for output in self:
      output.Fade(rgb_triplet, steps=steps)

  def Instant(self, rgb_triplet):
    """Immediately changes all connected outputs to the given `rgb_triplet`."""
    self.AllOutputs(rgb_triplet)

  # ############################################################################
  # Functions that need to be implemented to complete this abstract class
  #
  def SingleOutput(self, ident, color):
    raise NotImplementedError

  def AllOutputs(self, color):
    raise NotImplementedError

  def _DetectFrequency(self):
    raise NotImplementedError

  def _Heartbeat(self):
    raise NotImplementedError

  def _Verify(self):
    raise NotImplementedError


class JTagController(ColorController):
  ALL_OUTPUTS = '#%d,%d,%d\r\n'
  SINGLE_OUTPUT = '$%d,%d,%d,%d\r\n'
  HEARTBEAT = 'H\r\n'
  RESPONSE = 'R\r\n'

  @classmethod
  def Connect(cls, device):
    """Returns a JTagController instance connected to the given serial device.

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
        conn.write(cls.ALL_OUTPUTS % BLACK)
        if conn.read(3) == cls.RESPONSE:
          break
      else:
        raise ConnectionError('Device is not a proper %s.' % cls.__name__)
      print 'Initialization time: %.2f' % (time.time() - begin)
      print 'Connected to %s' % device
      return cls(conn)
    except serial.SerialException:
      raise ConnectionError('Could not open device %s.' % device)

  def AllOutputs(self, color):
    self.Command(self.ALL_OUTPUTS % color)

  def SingleOutput(self, output, color):
    self.Command(self.SINGLE_OUTPUT % ((output,) + color))

  def _DetectFrequency(self):
    """Returns the number of commands the controller handles in one second."""
    begin_time = time.time()
    frequency = 0
    while time.time() - begin_time < 1:
      self.AllOutputs(BLACK)
      frequency += 1
    print 'Controller frequency set to %dHz' % frequency
    return frequency

  def _Heartbeat(self):
    """Sends a heartbeat signal to the controller without verifying response."""
    self.Command(self.HEARTBEAT, verify=False)

  def _Verify(self):
    """Verifies the proper response from the JTAG ColorController."""
    response = self.serial.read(len(self.RESPONSE))
    if response != self.RESPONSE:
      raise ConnectionError('Incorrect acknowledgment: expected %r got: %r.' % (
          self.RESPONSE, response))


def main():
  """Quick example demo that cycles colors for strip 0."""
  def Pause(controller):
    """Snaps the outputs to black and allows for a short wait between demos."""
    time.sleep(.2)
    controller.Instant(BLACK)
    time.sleep(1)

  print 'Demonstration program for the ColorController class and JTAG\'s box.\n'
  controller = JTagController.ConnectFirst()
  print '\n1) Switching all outputs through red, green, blue ...'
  for color in [RED, BLACK, GREEN, BLACK, BLUE, BLACK] * 3:
    controller.Instant(color)
    time.sleep(.4)
  print '2) Fading all outputs through pure red, green, and blue ...'
  Pause(controller)
  for color in (RED, GREEN, BLUE, BLACK):
    controller.Fade(color)
    time.sleep(2.2)
  print '3) Double-blinking random outputs for 10 seconds ...'
  Pause(controller)
  for _count in range(30):
    controller.Random().Blink(utils.RandomTriplet(darken=True), 2)
    time.sleep(.35)
  print '4) Instantly changing colors on random outputs 1000x ...'
  Pause(controller)
  begin = time.time()
  for _count in range(1000):
    controller.Random().Instant(utils.RandomTriplet(darken=True))
    time.sleep(0.01)
  print '   1000 instant color changes took %.1fs.' % (time.time() - begin)
  print '5) Sequentialy fading to random colors at 500ms intervals ...'
  Pause(controller)
  print '\nThis is the last demonstration program, enjoy your blinky lights :-)'
  while True:
    controller.Next().Fade(utils.RandomTriplet(darken=True))
    time.sleep(.5)
    if not random.randrange(50):
      time.sleep(1)
      controller.Fade(utils.RandomTriplet(darken=True), 80)
      time.sleep(4)


if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print ''
    sys.exit()
