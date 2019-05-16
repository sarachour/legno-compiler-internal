
#include "Arduino.h"

#ifndef ANALOG_LIB1_API_H
#define ANALOG_LIB1_API_H

extern size_t dynamic_memory;

#define LEVEL 3
#define LOG_LEVEL 2
#define DEBUG_LEVEL 4
#define INFO_LEVEL 3

extern char FMTBUF[64];

template <typename type>
void tally_dyn_mem(
	const char * name
) {
	dynamic_memory += sizeof(type);
	// Serial.print(sizeof(type));
	// Serial.print('\t');
	// Serial.println(name);
}

static void print_log (const char * message) {
  // trap for printing error
  if(LEVEL >= LOG_LEVEL){
    Serial.print("AC:>[msg] ");
    Serial.println(message);
    Serial.flush();
  }
}
static void print_info (const char * message) {
  // trap for printing error
  if(LEVEL >= INFO_LEVEL){
    Serial.print("AC:>[msg] ");
    Serial.println(message);
    Serial.flush();
  }
}
static void print_debug (const char * message) {
  // trap for printing error
  if(LEVEL >= DEBUG_LEVEL){
    Serial.print("AC:>[msg] ");
    Serial.println(message);
    Serial.flush();
  }
}

static void print_level(const char * message, int level){
  switch(level){
  case LOG_LEVEL: print_log(message); break;
  case DEBUG_LEVEL: print_debug(message); break;
  case INFO_LEVEL: print_info(message); break;
  }
}
static void error (
                   const char * message
                   ) {
  // trap for printing error
  while(true){
    Serial.print("AC:>[msg] ERROR: ");
    Serial.println(message);
    Serial.flush();
    delay(1000);
  }
}

// how much to delay before measurement and how many times to measure
#define CAL_REPS 65536
#define FULL_SCALE 1.2
#endif

#ifndef _PIN
#define _PIN
#include "pin.h"
#endif

#ifndef _FABRIC
#define _FABRIC
#include "fabric.h"
#endif

#ifndef _CHIP
#define _CHIP
#include "chip.h"
#endif

#ifndef _TILE
#define _TILE
#include "tile.h"
#endif

#ifndef _SLICE
#define _SLICE
#include "slice.h"
#endif

#ifndef _FU
#define _FU
#include "fu.h"
#endif

#ifndef _CHIP_INOUT
#define _CHIP_INOUT
#include "chipInOut.h"
#endif

#ifndef _DAC
#define _DAC
#include "dac.h"
#endif

#ifndef _MUL
#define _MUL
#include "mul.h"
#endif

#ifndef _INT
#define _INT
#include "int.h"
#endif

#ifndef _FAN
#define _FAN
#include "fan.h"
#endif

#ifndef _ADC
#define _ADC
#include "adc.h"
#endif

#ifndef _LUT
#define _LUT
#include "lut.h"
#endif

#ifndef _TILE_INOUT
#define _TILE_INOUT
#include "tileInOut.h"
#endif

#ifndef _CONNECTION
#define _CONNECTION
#include "connection.h"
#endif

#ifndef _VECTOR
#define _VECTOR
#include "vector.h"
#endif

#ifndef _SPI
#define _SPI
#include "spi.h"
#endif

