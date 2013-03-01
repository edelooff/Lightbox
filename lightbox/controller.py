#!/usr/bin/python
"""Lightbox library for hardware controllers

This module contains the basic controller interface and output management.
"""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '2.0'

# Standard modules
import random
import serial
import threading
import time

# Application modules
from . import light
from . import utils

BLACK = 0, 0, 0


class ConnectionError(Exception):
  """A problem connecting to the USB serial light controller."""


class Heartbeat(threading.Thread):
  """Heartbeat keepalive thread to keep the Lightbox controller online."""
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
        time.sleep(self.delay)
      except ConnectionError:
        time.sleep(self.fail_delay)


class BaseController(list):
  """Base class for a Lightbox controller."""
  def __init__(self, conn_info, outputs=5, output_cls=light.Output):
    """Initializes the BaseController for Lightbox."""
    super(BaseController, self).__init__()
    self.last_output_id = -1
    self.lock = threading.Lock()
    self.output_cls = output_cls
    self.connection = self._Connect(conn_info)
    self.frequency = self._DetectFrequency()
    Heartbeat(self._Heartbeat)
    for _num in range(outputs):
      self.Add()

  # ############################################################################
  # Info methods, some to be overridden for differing devices.
  #
  def Info(self):
    """Returns a dictionary of Lightbox controller info."""
    return {'controller': type(self).__name__,
            'device': self._DeviceInfo(),
            'commandRate': {
                'combined': self.frequency,
                'perOutput': float(self.frequency) / len(self)},
            'layerBlenders': utils.BLENDERS,
            'outputActions': self.output_cls.ACTIONS,
            'outputCount': len(self),
            'transitionEnvelopes': utils.ENVELOPES}

  def _DeviceInfo(self):
    """Returns a batch of hardware-specific info."""
    return {'type': 'serial',
            'baudrate': self.connection.baudrate,
            'port': self.connection.port}

  # ############################################################################
  # Connecting to attached hardware, also a convencience 'attempt to connect'
  #
  @classmethod
  def FirstDevice(cls, outputs=5):
    """Attempts to connect to first 10 USB serial devices."""
    for usb_index in range(10):
      conn_info = {'device': '/dev/ttyUSB%d' % usb_index}
      try:
        return cls(conn_info, outputs=outputs)
      except ConnectionError:
        pass
    raise ConnectionError('No suitable device found :(')

  def _Connect(self, conn_info):
    """Connects to the given serial device."""
    try:
      conn = serial.Serial(port=conn_info['device'],
                           baudrate=conn_info.get('baudrate', 9600),
                           timeout=conn_info.get('timeout', .5))
      conn.flushInput()
      print 'Connecting to %s' % conn_info['device']
      return conn
    except serial.SerialException:
      raise ConnectionError('Could not open device %s.' % conn_info['device'])

  # ############################################################################
  # Output add/removal
  #
  def Add(self):
    """Adds an output to the controller."""
    self.append(self.output_cls(self, len(self)))
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
    output = super(BaseController, self).__getitem__(index)
    self.last_output_id = index
    return output

  def append(self, item):
    """Overridden to only allow appending instances of self.output_cls."""
    if not isinstance(item, self.output_cls):
      raise TypeError('Can only add proper output objects to the controller.')
    super(BaseController, self).append(item)

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
  # Command options for the hardware
  #
  def Command(self, command, verify=True):
    """Send the command to the serial device and wait for the confirmation."""
    with self.lock:
      self._Command(command)
      if verify:
        self._Verify()

  def SetAll(self, color):
    """Sets the color for all outputs."""
    raise NotImplementedError

  def SetSingle(self, ident, color):
    """Sets the color for a single numbered output."""
    raise NotImplementedError

  # ############################################################################
  # Methods to be implemented or overridden by subclasses
  #
  def _Command(self, command):
    """Sends the given command to the device over the serial connection."""
    try:
      self.connection.write(command)
    except serial.SerialException:
      raise ConnectionError('Could not send command.')

  def _DetectFrequency(self):
    """Routine to auto-detect the frequency of the attached controller.

    This works for devices that give an acknowledgment of the given command.
    """
    raise NotImplementedError

  def _Heartbeat(self):
    """Command that is executed by the heartbeat thread if it operates."""
    raise NotImplementedError

  def _Verify(self):
    """Verifies the repsonse received from the hardware is correct."""
    raise NotImplementedError


class Dummy(BaseController):
  """A dummy controller that doesn't connect to any device.

  This is useful for testing all the other parts of Lightbox when the required
  hardware is not available.
  """
  @classmethod
  def FirstDevice(cls, outputs=5):
    """Returns a functional Dummy controller."""
    return cls(None, outputs=outputs)

  def _Command(self, _command):
    """Dummy controller doesn't perform commands."""

  def _Connect(self, conn_info):
    """Connecting to a Dummy controller never fails to connect."""

  def _DetectFrequency(self):
    """Dummy controller has a set frequency."""
    return 100

  def _DeviceInfo(self):
    """Device info for the dummy is short and sweet."""
    return {'type': 'dummy'}

  def _Heartbeat(self):
    """Dummy controller has no heartbeat."""

  def _Verify(self):
    """Dummy controller doesn't verify."""

  def SetAll(self, color):
    """Dummy controller doesn't perform commands."""

  def SetSingle(self, ident, color):
    """Dummy controller doesn't perform commands."""


class JTagController(BaseController):
  """The Lightbox controller as realised for the Twitterboom project.

  The controller accepts commands over a 57k6 serial connection. The protocol
  is easy to understand and readable in plain text:

  * To set all the outputs to a single color:
    Write a '#' followed by the red channel value from 0 to 255 (with the digits
    written out), followed by a comma and the value for green, followed by a
    comma and the value for blue, ended by a carriage-return line-feed (CR-LF).
  * To set a single output to a color:
    Write a '$' followed by the channel number (0 to 4), a comma and the red,
    green and blue values as above, ended by a CR-LF as above.
  * Both of these commands receive a reply from the controller. The reply is a
    capital 'R' ended by a CR-LF.
  * Every five seconds (though actual timeout occurs after ten), a 'heartbeat'
    should be sent. This consists of a capital 'H' followed by a CR-LF.
  """
  ALL_OUTPUTS = '#%d,%d,%d\r\n'
  HEARTBEAT = 'H\r\n'
  RESPONSE = 'R\r\n'

  def _Connect(self, conn_info):
    """Returns a tested and confirmed serial connection to the hardware.

    We're waiting for a second after opening the device, this is because the
    LED controller needs some time before it behaves properly.
    """
    conn_info['baudrate'] = 57600
    conn = super(JTagController, self)._Connect(conn_info)
    for _attempt in range(5):
      conn.write(self.ALL_OUTPUTS % BLACK)
      if conn.read(3) == self.RESPONSE:
        return conn
    else:
      raise ConnectionError('Device on port %s not a proper %s.' % (
          conn_info['device'], type(self).__name__))

  def _DetectFrequency(self):
    """Returns the number of commands the controller handles in one second."""
    begin_time = time.time()
    frequency = 0
    while time.time() - begin_time < 1:
      self.SetAll(BLACK)
      frequency += 1
    print 'Controller frequency set to %dHz' % frequency
    return frequency

  def _Heartbeat(self):
    """Sends a heartbeat signal to the controller without verifying response."""
    self.Command(self.HEARTBEAT, verify=False)

  def _Verify(self):
    """Verifies the proper response from the Lightbox controller hardware."""
    response = self.connection.read(len(self.RESPONSE))
    if response != self.RESPONSE:
      raise ConnectionError('Incorrect acknowledgment: expected %r got: %r.' % (
          self.RESPONSE, response))

  def SetAll(self, color):
    """Sets all outputs to the same color."""
    self.Command(self.ALL_OUTPUTS % tuple(color))

  def SetSingle(self, output, color):
    """Sets a single output to a given color."""
    self.Command('$%d,%s\r\n' % (output, ','.join(map(str, color))))
