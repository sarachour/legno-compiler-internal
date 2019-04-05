#ifndef PINS_H
#define PINS_H

#include "Arduino.h"
#include "include/Util.h"
#include "include/Globals.h"
#define ALPHA -0.001592251629
#define BETA 3.267596063219

const unsigned char PIN_ctrRst= 2; /*ctrRst*/
const unsigned char PIN_spiClk = 7; /*spi clk*/
const unsigned char PIN_spiMosi= 8; /*spi master out slave in*/
const unsigned char PIN_moMiEn= 13; /*moMiEn*/

/*ANALOG INPUT CHANNEL ENABLE PINS*/
// 26 : (0,3,2)
// 27 : (0,3,3)
// 28 : (0,3,2)
// 29: (1,3,3)

const unsigned char PIN_anaLoc[4][3] = {
  {0,3,2},
  {0,3,3},
  {1,3,2},
  {1,3,3}
};

const unsigned char PIN_anaEn[4] = {26,27,28,29};
const unsigned char PIN_anaOut[4] = {6,4,2,0};
const unsigned char PIN_chipSel[2]= {30,31};
const unsigned char PIN_rowSel[2] = {25,23};
const unsigned char PIN_colSel[2] = {24,22};

const unsigned char PIN_spiSSPin[2][4] = {
  {3,4,5,6},
  {50,1,2,3}
};

const unsigned char PIN_spiMiso[2][4] = {
  {9,10,11,12},
  {14,15,16,17}
    };


const unsigned char PIN_tdiClk = 32;
const unsigned char PIN_tdi[8] = {35,37,39,41,43,45,47,49};
const unsigned char PIN_tdoClk = 34;
const unsigned char PIN_tdo[8] = {34,36,38,40,42,44,46,48};

#ifdef _DUE
static inline void DigitalWriteP(unsigned char pin, unsigned char val) {
if (val) g_APinDescription[pin].pPort -> PIO_SODR = g_APinDescription[pin].ulPin;
 else g_APinDescription[pin].pPort -> PIO_CODR = g_APinDescription[pin].ulPin;
}

static inline unsigned char DigitalReadP(unsigned char pin) {
return !!(g_APinDescription[pin].pPort -> PIO_PDSR & g_APinDescription[pin].ulPin);
}
#else
static inline void DigitalWriteP(unsigned char pin, unsigned char val){
digitalWrite(pin,val);
}
static inline unsigned char DigitalReadP(unsigned char pin){
return digitalRead(pin);
}
#endif

void setup_io();
void setup_pins();
void pin_reset();
void set_pin(unsigned char pin, unsigned int value);

#endif
