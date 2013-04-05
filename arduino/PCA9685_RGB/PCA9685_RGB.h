#pragma once

#include <Arduino.h>
#include <Wire.h>
#include "lightness.h"

/* Section 7.3: Register definitions */
#define PCA9685_BASE_ADDRESS 0x40
#define PCA9685_MODE1 0x00
#define PCA9685_MODE2 0x01
#define PCA9685_ALLCALLADR 0x05
#define PCA9685_PRESCALE 0xFE
#define PCA9685_LED0 0x06

class PCA9685_RGB {
  public:
    PCA9685_RGB(byte pcaAddress = PCA9685_BASE_ADDRESS);
    byte pcaAddress;
    void
      begin(),
      setAll(const byte red, const byte green, const byte blue),
      setAll(const byte greyscale),
      setLed(const byte led, const byte red, const byte green, const byte blue),
      setLed(const byte led, const byte greyscale);

  private:
    const static byte outputs = 5;
    void
      writeRegister(byte regAddress, byte regData),
      setGroupLevels(byte group, pwm_grey_t levels),
      setGroupLevels(byte group, pwm_rgb_t levels);
};
