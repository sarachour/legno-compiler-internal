#ifndef CALIB_RESULT_H
#define CALIB_RESULT_H

#define SIZE2D 9
#define SIZE1D (SIZE2D*SIZE2D)
#define MAX_KEYS SIZE1D

#include "float16.h"

#define size(n) (n*11+1+2)

typedef struct {
  uint16_t bias[MAX_KEYS];
  uint16_t noise[MAX_KEYS];
  uint16_t target[MAX_KEYS];
  uint16_t input0[MAX_KEYS];
  uint16_t input1[MAX_KEYS];
  unsigned char size;
  unsigned char port[MAX_KEYS];
} profile_t;

typedef union {
  profile_t result;
  unsigned char charbuf[size(MAX_KEYS)];
} serializable_profile_t;

namespace prof {

  extern profile_t TEMP;

  int size_1d();
  int size_2d();
  int data_1d(float* data,int size);
  int data_2d(float* data,int size);
  void print_profile(profile_t& result, int level);

  void init_profile(profile_t& result);
  void add_prop(profile_t& profile,
                unsigned char prop,
                float target,
                float input0,
                float input1,
                float bias,
                float noise);
}
#endif
