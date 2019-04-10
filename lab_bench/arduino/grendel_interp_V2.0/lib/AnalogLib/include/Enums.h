#ifndef ENUM_H
#define ENUM_H

typedef enum _RANGE_TYPE {
  RNG_LOW,
  RNG_MED,
  RNG_HIGH
} RANGE_TYPE;

typedef enum _SIGN_TYPE {
  POS,
  NEG
} SIGN_TYPE;

#define LEFT 0
#define RIGHT 1

typedef enum _PORT {
  COEFF,
  IN0,
  IN1,
  IC,
  OUT0,
  OUT1,
  OUT2,
  UNKNOWN_PORT
} PORT_NAME;

typedef enum _BLOCK {
  MULT,
  TILE_DAC,
  TILE_ADC,
  TILE_LUT,
  INTEG,
  FANOUT,
  TILE_IN,
  TILE_OUT,
  CHIP_IN,
  CHIP_OUT,
  UNKNOWN_BLOCK
} BLOCK_TYPE;

typedef struct _BLOCK_LOC_DATA {
  unsigned char chip;
  unsigned char tile;
  unsigned char slice;
  unsigned char index;
  BLOCK_TYPE type;
} block_loc_t;


#endif
