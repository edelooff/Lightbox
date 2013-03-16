// Wire libary I2C speed is 400kHz instead of default 100kHz.
// This is done by copying the Wire library to the Arduino
// 'libraries' folder and editing the 'utility/twi.h' file.
#include <Wire.h>
#include <PCA9685_RGB.h>

const char
  typeAllColor = '\x01',
  typeOneColor = '\x02',
  typeAllGray  = '\x03',
  lengthAllColor = '\x03',
  lengthOneColor = '\x04',
  lengthAllGray  = '\x01';
PCA9685_RGB controller = PCA9685_RGB();

// Declare functions to benefit commandline compiling
bool readByte(byte &receivedByte);
void commandAllOutputs(void);
void commandGrayScale(void);
void commandSingleOutput(void);

void setup(void) {
  Wire.begin();
  controller.begin();
  controller.setAll(0);
  Serial.begin(57600);
  // Tell the connecting side that this is a Lightbox.
  Serial.println("[Lightbox]");
}

void loop(void) {
  byte receivedByte;
  if (readByte(receivedByte)) {
    switch (receivedByte) {
      case typeAllColor:
        commandAllOutputs();
        break;
      case typeOneColor:
        commandSingleOutput();
        break;
      case typeAllGray:
        commandGrayScale();
        break;
      default:
        // Bad command TYPE, turn off all inputs
        controller.setAll(0);
    }
  }
}

void commandAllOutputs(void) {
  // Sets an RGB color for all outputs on the Lightbox.
  byte receivedByte, red, green, blue;
  // Verify payload length, if correct, read payload and set colors.
  if (readByte(receivedByte) && receivedByte == lengthAllColor)
    if (readByte(red) && readByte(green) && readByte(blue))
      controller.setAll(red, green, blue);
}

void commandSingleOutput(void) {
  // Sets an RGB color for a single output of the Lightbox.
  const byte outputs = 5;
  byte receivedByte, red, green, blue, output;
  // Verify payload length, if correct, read payload and set output color.
  if (readByte(receivedByte) && receivedByte == lengthOneColor)
    if (readByte(output) && output < outputs &&
        readByte(red) && readByte(green) && readByte(blue))
      controller.setLed(output, red, green, blue);
}

void commandGrayScale(void) {
  // Sets a grayscale level for all outputs on the Lightbox.
  byte receivedByte, level;
  // Verify payload length, if correct, set controller output level
  if (readByte(receivedByte) && receivedByte == lengthAllGray)
    if (readByte(level))
      controller.setAll(level);
}

bool readByte(byte &receivedByte) {
  // Read a single byte from Serial, with a global read timeout.
  const byte readTimeout = 10;
  long starttime = millis();
  while (!Serial.available())
    if ((millis() - starttime) > readTimeout)
      return false;
  receivedByte = Serial.read();
  return true;
}
