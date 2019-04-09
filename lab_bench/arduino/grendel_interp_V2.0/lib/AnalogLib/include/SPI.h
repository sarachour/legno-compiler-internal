#include "include/Pin.h"
namespace spi {
static inline void spiBit (bool sendBit) {
	/*clock low*/
  pin::DigitalWriteP(PIN_spiClk, LOW);
  pin::DigitalWriteP(PIN_spiMosi, sendBit);
  pin::DigitalWriteP(PIN_spiClk, HIGH);
}

static inline void spiDrive (
	unsigned char selRow,
	unsigned char selCol,
	unsigned char selLine,
	unsigned char cfgTile
) {
	/*write the tile signature, 0101*/
	spiBit(false);spiBit(true);spiBit(false);spiBit(true);

        /*from selRow*/
        spiBit((selRow&0x8)>>3);
        spiBit((selRow&0x4)>>2);
        spiBit((selRow&0x2)>>1);
        spiBit((selRow&0x1)>>0);
        /*from selCol*/
        spiBit((selCol&0x8)>>3);
        spiBit((selCol&0x4)>>2);
        spiBit((selCol&0x2)>>1);
        spiBit((selCol&0x1)>>0);
        /*from selLine*/
        spiBit((selLine&0x8)>>3);
        spiBit((selLine&0x4)>>2);
        spiBit((selLine&0x2)>>1);
        spiBit((selLine&0x1)>>0);
        /*from cfgTile*/
        spiBit((cfgTile&0x80)>>7);
        spiBit((cfgTile&0x40)>>6);
        spiBit((cfgTile&0x20)>>5);
        spiBit((cfgTile&0x10)>>4);
        spiBit((cfgTile&0x08)>>3);
        spiBit((cfgTile&0x04)>>2);
        spiBit((cfgTile&0x02)>>1);
        spiBit((cfgTile&0x01)>>0);
}

/*send single bit to HCDC chip*/

/*send binary instruction to HCDC chip*/
static inline int spiDrive (const bool * vector, int spiMisoPin) {

	// Serial.print("spiDrive spiMisoPin = "); Serial.println(spiMisoPin);
	int misoBuffer = 0;

	/*loop over bit*/
	for (unsigned char bitIndex=0; bitIndex<24; bitIndex++) {
		/*write output and read input*/
		/*clock low*/
    DigitalWriteP(PIN_spiClk, LOW);
    DigitalWriteP(PIN_spiMosi, vector[bitIndex]);

		/*read the SPI MISO bit*/
		// if input is high, add to buffer
		/*bits are streamed out lsb first*/
    bitWrite(misoBuffer, bitIndex, DigitalReadP(spiMisoPin));
		// Serial.print("misoBuffer = "); Serial.println(misoBuffer);

		/*clock high*/
    DigitalWriteP(PIN_spiClk, HIGH);

	}

	/*print*/
	// Serial.println("MISO from HCDC:");
	// Serial.println(misoBuffer);
	return misoBuffer;
}

}
