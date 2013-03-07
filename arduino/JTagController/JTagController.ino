// Wire libary I2C speed is 400kHz instead of default 100kHz.
// This is done by copying the Wire library to the Arduino
// 'libraries' folder and editing the 'utility/twi.h' file.
#include <Wire.h>

const byte
  pcaBaseAddress = 0x40,
  pcaFirstLedOn  = 0x06,
  pcaFirstLedOff = 0x08,
  pcaMode1 = 0x00,
  pcaMode2 = 0x01;
const char
  *singleOutput = "$%3d,%3d,%3d,%3d",
  *allOutputs = "#%3d,%3d,%3d";
int errorCount = 0;

void setup() {
  Serial.begin(57600);
  Wire.begin();
  setupDriver();
  for (byte output = 16; output-- > 0;)
    setOutputLevel(output, 0);
}

void loop() {
  char receiveBuffer[20];
  int output, red, green, blue;
  receiveBuffer[0] = 0;
  if (readLine(receiveBuffer, 1000)) {
    if (strlen(receiveBuffer) > 4) {
      if (receiveBuffer[0] == '$') {
        sscanf(receiveBuffer, singleOutput, &output, &red, &green, &blue);
        output *= 3;
        setOutputLevel(output++, red);
        setOutputLevel(output++, green);
        setOutputLevel(output++, blue);
      } else {
        sscanf(receiveBuffer, allOutputs, &red, &green, &blue);
        for (byte j = 5; j-- > 0;) {
          output = j * 3;
          setOutputLevel(output++, red);
          setOutputLevel(output++, green);
          setOutputLevel(output++, blue);
        }      
      }
      Serial.println('R');
    } else if (receiveBuffer[0] == 'H') {
      errorCount = 0;
    }
  } else if (++errorCount > 10) {
      // No transmission for 10 seconds, everything dark.
      for (byte output = 16; output-- > 0;)
        setOutputLevel(output, 0);
  };
}

boolean readLine(char *line, int timeout) {
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

void setupDriver() {
  // Sets the correct register values for the PCA9685 driver.
  writeRegister(pcaMode1, B00100000);
  writeRegister(pcaMode2, B00000100);
}
  
void writeRegister(byte regAddress, byte regData) {
  Wire.beginTransmission(pcaBaseAddress);
  Wire.write(regAddress);
  Wire.write(regData);
  Wire.endTransmission();
}

void setOutputLevel(byte output, byte level) {
  int intensity;
   if (level)
     intensity = level * 16;
    else
      intensity = 1;
  Wire.beginTransmission(pcaBaseAddress);
  // Only write OFF registers, skip ON registers.
  // This means all PWM load starts at zero, which is not ideal
  // but will have to do for the moment.
  Wire.write(pcaFirstLedOff + 4 * output);
  Wire.write(lowByte(intensity));  // OFF_LOW
  Wire.write(highByte(intensity)); // OFF_HIGH
  Wire.endTransmission();
}
