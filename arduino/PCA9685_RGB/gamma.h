#pragma once

#include <Arduino.h>

struct pwm_grey_t {
  byte int_lo, int_hi;
};

struct pwm_rgb_t {
  byte red_lo, red_hi, green_lo, green_hi, blue_lo, blue_hi;
};

const pwm_grey_t gammaCorrect(byte level);
const pwm_rgb_t gammaCorrect(byte red, byte green, byte blue);
