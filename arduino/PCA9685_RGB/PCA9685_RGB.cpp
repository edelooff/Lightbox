#pragma once

#include "PCA9685_RGB.h"

const int PCA9685_RGB::groupOffset[5] = {0, 600, 1360, 2040, 2720};

PCA9685_RGB::PCA9685_RGB(byte pcaAddress): pcaAddress(pcaAddress) {}

void PCA9685_RGB::begin() {
  // Sets the correct register values for the PCA9685 driver.

  // Mode register 1 pin description:
  // bit 7: Restart
  // bit 6: Use external clock
  // bit 5: Enable register auto-increment
  // bit 4: Sleep
  // bit 3-0: Sub address response suppression (refer to datasheet)
  writeRegister(PCA9685_MODE1, B00100000);

  // Mode register 2 pin description:
  // bit 7-5: reserved
  // bit 4: Invert output logic states
  // bit 3: Outputs change on STOP (0) or ACK (1)
  // bit 2: Output: Open Drain (0) or Totem Pole (1)
  // bit 1-0: Apply output inversion magics (refer to datasheet)
  writeRegister(PCA9685_MODE2, B00000100); // These are all default values
  setAll(0, 0, 0); // Set all outputs to OFF
  delay(50);
}

void PCA9685_RGB::setAll(const byte red, const byte green, const byte blue) {
  pwm_rgb_t levels = gammaCorrect(red, green, blue);
  byte pwm_on_lo = 0, pwm_on_hi = 0;
  Wire.beginTransmission(pcaAddress);
  Wire.write(PCA9685_LED0);
  for (byte output = 5; output-- > 0;) {
    Wire.write(pwm_on_lo);
    Wire.write(pwm_on_hi);
    Wire.write(levels.red_lo);
    Wire.write(levels.red_hi);
    Wire.write(pwm_on_lo);
    Wire.write(pwm_on_hi);
    Wire.write(levels.green_lo);
    Wire.write(levels.green_hi);
    Wire.write(pwm_on_lo);
    Wire.write(pwm_on_hi);
    Wire.write(levels.blue_lo);
    Wire.write(levels.blue_hi);
  }
  Wire.endTransmission();
}

void PCA9685_RGB::setAll(const byte greyscale) {
  pwm_grey_t levels = gammaCorrect(greyscale);
  byte pwm_on_lo = 0, pwm_on_hi = 0;
  Wire.beginTransmission(pcaAddress);
  Wire.write(PCA9685_LED0);
  for (byte pin = 15; pin-- > 0;) {
    Wire.write(pwm_on_lo);
    Wire.write(pwm_on_hi);
    Wire.write(levels.int_lo);
    Wire.write(levels.int_hi);
  }
  Wire.endTransmission();
}

void PCA9685_RGB::setLed(const byte led, const byte red, const byte green, const byte blue) {
  pwm_rgb_t levels = gammaCorrect(red, green, blue);
  byte pwm_on_lo = 0, pwm_on_hi = 0;
  Wire.beginTransmission(pcaAddress);
  Wire.write(PCA9685_LED0 + 12 * led);
  Wire.write(pwm_on_lo);
  Wire.write(pwm_on_hi);
  Wire.write(levels.red_lo);
  Wire.write(levels.red_hi);
  Wire.write(pwm_on_lo);
  Wire.write(pwm_on_hi);
  Wire.write(levels.green_lo);
  Wire.write(levels.green_hi);
  Wire.write(pwm_on_lo);
  Wire.write(pwm_on_hi);
  Wire.write(levels.blue_lo);
  Wire.write(levels.blue_hi);
  Wire.endTransmission();

}

void PCA9685_RGB::setLed(const byte led, const byte greyscale) {
  pwm_grey_t levels = gammaCorrect(greyscale);
  byte pwm_on_lo = 0, pwm_on_hi = 0;
  Wire.beginTransmission(pcaAddress);
  Wire.write(PCA9685_LED0 + 12 * led);
  for (byte pin = 3; pin-- > 0;) {
    Wire.write(pwm_on_lo);
    Wire.write(pwm_on_hi);
    Wire.write(levels.int_lo);
    Wire.write(levels.int_hi);
  }
  Wire.endTransmission();
}

void PCA9685_RGB::writeRegister(byte regAddress, byte regData) {
  // Writes register values for the PCA9685 driver
  Wire.beginTransmission(pcaAddress);
  Wire.write(regAddress);
  Wire.write(regData);
  Wire.endTransmission();
}
