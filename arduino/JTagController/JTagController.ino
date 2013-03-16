// Wire libary I2C speed is 400kHz instead of default 100kHz.
// This is done by copying the Wire library to the Arduino
// 'libraries' folder and editing the 'utility/twi.h' file.
#include <Wire.h>
#include <PCA9685_RGB.h>

// Declare functions to benefit commandline compiling
bool readLine(char *line);

PCA9685_RGB controller = PCA9685_RGB();

void setup(void) {
  Wire.begin();
  controller.begin();
  controller.setAll(0);
  Serial.begin(57600);
  // Tell the connecting side that this is a Lightbox.
  Serial.println("[Lightbox]");
}

void loop(void) {
  const char
    *singleOutput = "$%3d,%3d,%3d,%3d",
    *allOutputs = "#%3d,%3d,%3d";
  char receiveBuffer[20];
  static byte errorCount = 0;
  byte output, red, green, blue;
  receiveBuffer[0] = 0;
  if (readLine(receiveBuffer)) {
    if (strlen(receiveBuffer) > 4) {
      if (receiveBuffer[0] == '$') {
        sscanf(receiveBuffer, singleOutput, &output, &red, &green, &blue);
        controller.setLed(output, red, green, blue);
      } else {
        sscanf(receiveBuffer, allOutputs, &red, &green, &blue);
        controller.setAll(red, green, blue);
      }
      Serial.println('R');
    } else if (receiveBuffer[0] == 'H') {
      errorCount = 0;
    }
  } else if (++errorCount > 10) {
      // No transmission for 10 seconds, everything dark.
      controller.setAll(0);
  };
}

bool readLine(char *line) {
  const int timeout = 1000;
  byte receivedByte;
  long starttime = millis();
  while (receivedByte != '\n') {
    while (!Serial.available())
      if ((millis() - starttime) > timeout)
        return false;
    receivedByte = Serial.read();
    if (receivedByte != '\r') // Ignore carriage return.
      *line++ = receivedByte;
  }
  *line = 0;
  return true;
}
