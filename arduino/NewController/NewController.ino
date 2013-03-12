// Wire libary I2C speed is 400kHz instead of default 100kHz.
// This is done by copying the Wire library to the Arduino
// 'libraries' folder and editing the 'utility/twi.h' file.
#include <Wire.h>
#include "gammacorrect.h"

const byte
  characterTimeout = 10,
  outputs = 5,
  pcaBaseAddress = 0x40,
  pcaFirstLedOn  = 0x06,
  pcaFirstLedOff = 0x08,
  pcaMode1 = 0x00,
  pcaMode2 = 0x01,
  pcaAllLedOn  = 0xFA,
  pcaAllLedOff = 0xFC;
const int commandTimeout = 1000;

void setup(void) {
  Wire.begin();
  setupDriver();
  for (byte pin = 16; pin-- > 0;)
    setPcaPinLevel(pin, 0);
  Serial.begin(57600);
  // Tell the connecting side that this is a Lightbox.
  Serial.println("[Lightbox]");
}

void loop(void) {
  byte receivedByte;
  if (readByte(receivedByte, commandTimeout)) {
    switch (receivedByte) {
      case '\x01':
        commandAllOutputs();
        break;
      case '\x02':
        commandSingleOutput();
        break;
      case '\x03':
        commandGrayScale();
        break;
      default:
        // Bad command TYPE, turn off all inputs
        for (byte output = outputs; output-- > 0;)
          setOutputColor(output, 0, 0, 0);
    }
  }
}

void commandAllOutputs(void) {
  // Sets an RGB color for all outputs on the Lightbox.
  byte receivedByte, red, green, blue;
  // Verify payload length, if correct, read payload and set colors.
  if (readByte(receivedByte, characterTimeout) && receivedByte == '\x03')
    if (readByte(red, characterTimeout) &&
        readByte(green, characterTimeout) &&
        readByte(blue, characterTimeout))
      for (byte output = outputs; output-- > 0;)
        setOutputColor(output, red, green, blue);
}

void commandSingleOutput(void) {
  // Sets an RGB color for a single output of the Lightbox.
  byte receivedByte, red, green, blue, output;
  // Verify payload length, if correct, read payload and set output color.
  if (readByte(receivedByte, characterTimeout) && receivedByte == '\x04')
    if (readByte(output, characterTimeout) && output < outputs &&
        readByte(red, characterTimeout) &&
        readByte(green, characterTimeout) &&
        readByte(blue, characterTimeout))
      setOutputColor(output, red, green, blue);
}

void commandGrayScale(void) {
  // Sets a grayscale level for all outputs on the Lightbox.
  byte receivedByte, level;
  // Verify payload length, if correct, set controller output level
  if (readByte(receivedByte, characterTimeout) && receivedByte == '\x01')
    if (readByte(level, characterTimeout))
      setPcaPinLevelAll(level);
}

void setOutputColor(byte output, byte red, byte green, byte blue) {
  // Set the given output to the configured red, green and blue levels.
  output *= 3;
  setPcaPinLevel(output++, red);
  setPcaPinLevel(output++, green);
  setPcaPinLevel(output++, blue);
}

bool readByte(byte &receivedByte, int timeout) {
  // Read a single byte from Serial, with a provided timeout
  long starttime = millis();
  while (!Serial.available())
    if ((millis() - starttime) > timeout)
      return false;
  receivedByte = Serial.read();
  return true;
}

void setupDriver() {
  // Sets the correct register values for the PCA9685 driver.

  // Mode register 1 pin description:
  // bit 7: Restart
  // bit 6: Use external clock
  // bit 5: Enable register auto-increment
  // bit 4: Sleep
  // bit 3-0: Sub address response suppression (refer to datasheet)
  writeRegister(pcaMode1, B00100000);

  // Mode register 2 pin description:
  // bit 7-5: reserved
  // bit 4: Invert output logic states
  // bit 3: Outputs change on STOP (0) or ACK (1)
  // bit 2: Output: Open Drain (0) or Totem Pole (1)
  // bit 1-0: Apply output inversion magics (refer to datasheet)
  writeRegister(pcaMode2, B00000100); // These are all default values
}

void writeRegister(byte regAddress, byte regData) {
  // Writes register values for the PCA9685 driver
  Wire.beginTransmission(pcaBaseAddress);
  Wire.write(regAddress);
  Wire.write(regData);
  Wire.endTransmission();
}

void setPcaPinLevel(byte pin, byte level) {
  // Sets the 12-bit PWM pin value based on the 8-bit level input.
  int intensity = gammaCorrected(level);
  Wire.beginTransmission(pcaBaseAddress);
  // Only write OFF registers, skip ON registers.
  // This means all PWM load starts at zero, which is not ideal
  // but will have to do for the moment.
  Wire.write(pcaFirstLedOff + 4 * pin);
  Wire.write(lowByte(intensity));  // OFF_LOW
  Wire.write(highByte(intensity)); // OFF_HIGH
  Wire.endTransmission();
}

void setPcaPinLevelAll(byte level) {
  // Sets ALL 12-bit PWM pin values based on the 8-bit level input.
  int intensity = gammaCorrected(level);
  Wire.beginTransmission(pcaBaseAddress);
  Wire.write(pcaAllLedOff);
  Wire.write(lowByte(intensity));
  Wire.write(highByte(intensity));
  Wire.endTransmission();
}
