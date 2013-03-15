#pragma once

#include <Arduino.h>
#include <Wire.h>
#include "gamma.h"

#define PCA9685_ADDRESS 0x40

/* Section 7.3: Register definitions */
#define PCA9685_MODE1 0x00
#define PCA9685_MODE2 0x01
#define PCA9685_ALLCALLADR 0x05
#define PCA9685_PRESCALE 0xFE
#define PCA9685_LED0 0x6

class PCA9685_RGB {
  public:
    PCA9685_RGB(byte pcaAddress = PCA9685_ADDRESS);
    byte pcaAddress;
    void
      begin(),
      setAll(const byte red, const byte green, const byte blue),
      setAll(const byte greyscale),
      setLed(const byte led, const byte red, const byte green, const byte blue),
      setLed(const byte led, const byte greyscale);

  private:
    const static int groupOffset[5];
    void writeRegister(byte regAddress, byte regData);
//    void setPinPWM(byte pin, int step_on, int step_off);
//    void setGroupPWM(byte group, int step_on, int step_off);
};
