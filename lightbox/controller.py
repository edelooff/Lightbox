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


class BaseController(list):
  """Base class for a Lightbox controller."""
  FREQUENCY = 100
  GAMMA = 1
  LAYERS = 3
  OUTPUTS = 5
  VERIFY_COMMAND = True

  def __init__(self, conn_info, **kwds):
    """Initializes the BaseController for Lightbox."""
    super(BaseController, self).__init__()
    self.gamma_table = utils.GammaCorrectionList(kwds.get('gamma', self.GAMMA))
    self.last_output_id = -1
    self.layers = kwds.get('layers', self.LAYERS)
    self.lock = threading.Lock()
    self.output_cls = kwds.get('output_cls', light.Output)
    self.connection = self._Connect(conn_info)
    self._frequency = kwds.get('frequency', self.FREQUENCY)
    self._period = 1
    self.metronome = Metronome(self)
    for _num in range(kwds.get('outputs', self.OUTPUTS)):
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

  @staticmethod
  def _Connect(conn_info):
    """Connects to the given serial device."""
    try:
      print 'Connecting to %s' % conn_info['device']
      return serial.Serial(port=conn_info['device'],
                           baudrate=conn_info.get('baudrate', 9600),
                           timeout=conn_info.get('timeout', 0.25))
    except serial.SerialException:
      raise ConnectionError('Could not open device %s.' % conn_info['device'])

  # ############################################################################
  # Output add/removal
  #
  def Add(self):
    """Adds an output to the controller."""
    self.append(self.output_cls(layers=self.layers))
    self._UpdateOutputFrequency()

  def Remove(self):
    """Removes an output from the controller."""
    del_output = self.pop()
    del_output.InstantChange(BLACK)
    if del_output.output_id == self.last_output_id:
      self.last_output_id -= 1
    self._UpdateOutputFrequency()

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
  # Output frequency and period control
  #
  @property
  def frequency(self):
    """Returns the current frequency of the controller."""
    return self._frequency

  @frequency.setter
  def frequency(self, frequency):
    """Sets the new controller frequency, calculates per-output frequency."""
    self._frequency = frequency
    self._UpdateOutputFrequency()

  @property
  def period(self):
    """Returns the current per-output update period."""
    return self._period

  def _UpdateOutputFrequency(self):
    """Calculates the new per output command frequency.

    Also sets the period time for the Metronome.
    """
    if self:
      per_output_hz = float(self._frequency) / len(self)
      self._period = 1.0 / per_output_hz
      print 'Individual output frequency now %.1fHz' % per_output_hz
    else:
      print 'No outputs defined'
      self._period = 0.1

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
  def Command(self, command, verify=VERIFY_COMMAND):
    """Send the command to the serial device and wait for the confirmation."""
    with self.lock:
      self._Command(command)
      if verify:
        self._Verify()

  def SetAll(self, color):
    """Sets the color for all outputs."""
    self.Command(self._CommandSetAll(*[self.gamma_table[i] for i in color]))

  def SetSingle(self, output, color):
    """Sets the color for a single numbered output."""
    self.Command(self._CommandSetSingle(
        output, *[self.gamma_table[i] for i in color]))

  # ############################################################################
  # Methods to be implemented or overridden by subclasses
  #
  def _Command(self, command):
    """Sends the given command to the device over the serial connection."""
    try:
      self.connection.write(command)
    except serial.SerialException:
      raise ConnectionError('Could not send command.')

  def _CommandSetAll(self, red, green, blue):
    """Returns the command that sets all outputs to the same color."""
    raise NotImplementedError

  def _CommandSetSingle(self, output, red, green, blue):
    """Returns the command that sets a single output to a given color."""
    raise NotImplementedError

  def _Verify(self):
    """Verifies the repsonse received from the hardware is correct."""


class Heartbeat(threading.Thread):
  """Heartbeat keepalive thread to keep the Lightbox controller online."""
  def __init__(self, callback, delay=5, fail_delay=1):
    super(Heartbeat, self).__init__(name=type(self).__name__)
    self.beat = True
    self.callback = callback
    self.delay = delay
    self.fail_delay = fail_delay
    # Daemonize and run
    self.daemon = True
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


class Metronome(threading.Thread):
  """Sends color commands to the hardware for output objects on the controller.

  This ensures that all outputs are written briefly after eachother, without
  interleaving of commands that would happen if each output were to generate
  their own commands for the serial controller.
  """
  def __init__(self, controller):
    """Initializes the Metronome object."""
    super(Metronome, self).__init__(name=type(self).__name__)
    self.controller = controller
    # Daemonize and run
    self.daemon = True
    self.start()

  def run(self):
    """Updates outputs and sleeps the remaining time"""
    while True:
      begin_time = time.time()
      self._UpdateOutputs()
      self._SleepRemainder(begin_time)

  def _SleepRemainder(self, begin_time):
    """Sleeps for the remainder of this period."""
    remainder = begin_time + self.controller.period - time.time()
    if remainder > 0:
      time.sleep(remainder)

  def _UpdateOutputs(self):
    """Sends color commands for all outputs that have changed."""
    for index, output in enumerate(self.controller):
      color = output.NewColor()
      if color:
        self.controller.SetSingle(index, color)


# ##############################################################################
# Lightbox controller implementations
#
class Dummy(BaseController):
  """A dummy controller that doesn't connect to any device.

  This is useful for testing all the other parts of Lightbox when the required
  hardware is not available.
  """
  VERIFY_COMMAND = False

  @classmethod
  def FirstDevice(cls, outputs=5):
    """Returns a functional Dummy controller."""
    return cls(None, outputs=outputs)

  def _Command(self, _command):
    """Dummy controller doesn't perform commands."""

  def _CommandSetAll(self, *color):
    """Dummy controller doesn't perform commands."""

  def _CommandSetSingle(self, *args):
    """Dummy controller doesn't perform commands."""

  def _Connect(self, conn_info):
    """Connecting to a Dummy controller never fails to connect."""

  def _DeviceInfo(self):
    """Device info for the dummy is short and sweet."""
    return {'type': 'dummy'}


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
  ALL_OUTPUTS = '#%d,%d,%d\n'
  ONE_OUTPUT = '$%d,%d,%d,%d\n'
  HEARTBEAT = 'H\n'
  RESPONSE = 'R\r\n'

  def __init__(self, *args, **kwds):
    super(JTagController, self).__init__(*args, **kwds)
    self.frequency = self._DetectFrequency()
    Heartbeat(self._Heartbeat)

  def _CommandSetAll(self, *colors):
    """Sets all outputs to the same color."""
    return self.ALL_OUTPUTS % colors

  def _CommandSetSingle(self, *args):
    """Sets a single output to a given color."""
    return self.ONE_OUTPUT % args

  def _Connect(self, conn_info):
    """Returns a tested and confirmed serial connection to the hardware.

    After connecting, we attempt to send a command and verify the confirmation.
    This is tried a number of times, to allow for synchronization and/or boot
    requirements of the connected hardware.
    """
    conn_info['baudrate'] = 57600
    conn = super(JTagController, self)._Connect(conn_info)
    conn.flushInput()
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


class NewController(BaseController):
  """Lightbox controller optimized for minimal serial communication.

  The controller accepts commands over a 57k6 serial connection. The protocol
  for this controller is binary, as opposed to the human readable for the
  JTagController. The controller accepts two different commands, in TLV format:

  The first byte indicates the TYPE of command. The type value to set all
  outputs to a single color is `0x01`. The command to set a single output to a
  color is `0x02`.

  Following this type value is the LENGTH of the data. To set all outputs, three
  color bytes must follow and the length value is `0x03`. For single-output
  commands, the payload is 4 bytes (output, red, green, blue) and the length
  value comes out as `0x04`.

  Output and color values are written as single bytes in the range 0-4 and 0-255
  respectively.

  Commands may be at most 1000ms apart. After 10 missed commands (timeouts) the
  outputs on the controller turn dark. If individual characters in a command are
  more than 10ms apart, the command is discarded and retransmission must begin.

  Note that there are NO confirmations by the hardware. This maximizes
  throughput but reduces the opportunity for debugging.
  """
  FREQUENCY = 200
  ALL_OUTPUTS = '\x01\x03%c%c%c'
  ONE_OUTPUT = '\x02\x04%c%c%c%c'

  def _CommandSetAll(self, *colors):
    """Sets all outputs to the same color."""
    return self.ALL_OUTPUTS % colors

  def _CommandSetSingle(self, *args):
    """Sets a single output to a given color."""
    return self.ONE_OUTPUT % args

  def _Connect(self, conn_info):
    """Returns a tested and confirmed serial connection to the hardware.

    After connecting to the serial port, we pulse the DTR line once. This resets
    the Arduino hardware, which should as its first action after booting send
    the string [Lightbox] down the line.
    """
    conn_info['baudrate'] = 57600
    conn_info['timeout'] = 3 # We read once to confirm hardware; no perf. impact
    conn = super(NewController, self)._Connect(conn_info)
    # This resets the connected Arduino hardware
    conn.setDTR(True)
    conn.setDTR(False)
    if conn.readline().strip() != '[Lightbox]':
      raise ConnectionError('Device is not a [Lightbox].')
    return conn
