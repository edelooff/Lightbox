// Wire libary I2C speed is 400kHz instead of default 100kHz.
// This is done by copying the Wire library to the Arduino
// 'libraries' folder and editing the 'utility/twi.h' file.
#include <Wire.h>
#include <avr/pgmspace.h>

const byte
  characterTimeout = 10,
  outputs = 5,
  pcaBaseAddress = 0x40,
  pcaFirstLedOn  = 0x06,
  pcaFirstLedOff = 0x08,
  pcaMode1 = 0x00,
  pcaMode2 = 0x01;
const int commandTimeout = 1000;
PROGMEM prog_uint16_t gammaCorrected[256] = {
    // 8-bit intensity levels mapped to 12-bit PWM values corrected for the
    // non-linear sensitivity of the human eye. Gamma value = 2.2
    // Original function:
    //   gammaCorrected[i] = pow((float) i / 256, gamma) * 4096 + 1;
       0,    1,    1,    1,    1,    1,    2,    2,    3,    3,    4,    5,
       5,    6,    7,    8,   10,   11,   12,   14,   16,   17,   19,   21,
      23,   25,   27,   30,   32,   35,   37,   40,   43,   46,   49,   52,
      55,   59,   62,   66,   69,   73,   77,   81,   86,   90,   94,   99,
     104,  108,  113,  118,  123,  129,  134,  140,  145,  151,  157,  163,
     169,  175,  181,  188,  195,  201,  208,  215,  222,  229,  237,  244,
     252,  260,  268,  276,  284,  292,  300,  309,  317,  326,  335,  344,
     353,  363,  372,  382,  391,  401,  411,  421,  432,  442,  452,  463,
     474,  485,  496,  507,  518,  530,  541,  553,  565,  577,  589,  602,
     614,  626,  639,  652,  665,  678,  691,  705,  718,  732,  746,  760,
     774,  788,  803,  817,  832,  847,  862,  877,  892,  907,  923,  939,
     954,  970,  986, 1003, 1019, 1036, 1052, 1069, 1086, 1103, 1121, 1138,
    1156, 1173, 1191, 1209, 1227, 1246, 1264, 1283, 1302, 1320, 1339, 1359,
    1378, 1398, 1417, 1437, 1457, 1477, 1497, 1518, 1538, 1559, 1580, 1601,
    1622, 1643, 1665, 1686, 1708, 1730, 1752, 1774, 1797, 1819, 1842, 1865,
    1888, 1911, 1934, 1958, 1981, 2005, 2029, 2053, 2077, 2102, 2126, 2151,
    2176, 2201, 2226, 2251, 2277, 2302, 2328, 2354, 2380, 2406, 2433, 2459,
    2486, 2513, 2540, 2567, 2595, 2622, 2650, 2678, 2706, 2734, 2762, 2790,
    2819, 2848, 2877, 2906, 2935, 2965, 2994, 3024, 3054, 3084, 3114, 3145,
    3175, 3206, 3237, 3268, 3299, 3330, 3362, 3393, 3425, 3457, 3490, 3522,
    3554, 3587, 3620, 3653, 3686, 3719, 3753, 3786, 3820, 3854, 3888, 3923,
    3957, 3992, 4026, 4061};

void setup(void) {
  Wire.begin();
  setupDriver();
  for (byte pin = 16; pin-- > 0;)
    setDriverPinLevel(pin, 0);
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
      default:
        // Bad command TYPE, turn off all inputs
        for (byte output = outputs; output-- > 0;)
          setOutputColor(output, 0, 0, 0);
    }
  }
}

void messageAllOutputs(void) {
  byte receivedByte, red, green, blue;
  // Verify payload length, if correct, read payload and set colors.
  if (readByte(receivedByte, characterTimeout) && receivedByte == '\x03')
    if (readByte(red, characterTimeout) &&
        readByte(green, characterTimeout) &&
        readByte(blue, characterTimeout))
      for (byte output = outputs; output-- > 0;)
        setOutputColor(output, red, green, blue);
}

void messageSingleOutput(void) {
  byte receivedByte, red, green, blue, output;
  // Verify payload length, if correct, read payload and set output color.
  if (readByte(receivedByte, characterTimeout) && receivedByte == '\x04')
    if (readByte(output, characterTimeout) && output < outputs &&
        readByte(red, characterTimeout) &&
        readByte(green, characterTimeout) &&
        readByte(blue, characterTimeout))
      setOutputColor(output, red, green, blue);
}

void setOutputColor(byte output, byte red, byte green, byte blue) {
  // Set the given output to the configured red, green and blue levels.
  output *= 3;
  setDriverPinLevel(output++, red);
  setDriverPinLevel(output++, green);
  setDriverPinLevel(output++, blue);
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
  writeRegister(pcaMode1, B00100000);
  writeRegister(pcaMode2, B00000100);
}

void writeRegister(byte regAddress, byte regData) {
  // Writes register values for the PCA9685 driver
  Wire.beginTransmission(pcaBaseAddress);
  Wire.write(regAddress);
  Wire.write(regData);
  Wire.endTransmission();
}

void setDriverPinLevel(byte pin, byte level) {
  // Sets the 12-bit PWM pin value based on the 8-bit level input.
  int intensity = pgm_read_word_near(gammaCorrected + level);
  Wire.beginTransmission(pcaBaseAddress);
  // Only write OFF registers, skip ON registers.
  // This means all PWM load starts at zero, which is not ideal
  // but will have to do for the moment.
  Wire.write(pcaFirstLedOff + 4 * pin);
  Wire.write(lowByte(intensity));  // OFF_LOW
  Wire.write(highByte(intensity)); // OFF_HIGH
  Wire.endTransmission();
}
