#define _DUE
#include <HCDC_DEMO_API.h>

unsigned char HCDC_DEMO_BOARD = 2;

void setup() {

  Fabric fabric = Fabric();
  fabric.calibrate();

  unsigned char tileIndx = 3;
  unsigned char sliceIndx = 2;

  Fabric::Chip::Tile::Slice::Dac * DAC_A = fabric.chips[0].tiles[tileIndx].slices[sliceIndx + 1].dac;
  Fabric::Chip::Tile::Slice::FunctionUnit * tileout = &fabric.chips[0].tiles[tileIndx].slices[sliceIndx].tileOuts[0];

  unsigned short addr = 0;
  byte data[256];

  // for all the addresses in the LUT, sine table lookup
  do {
// Turn on the following for sine table lookup
    float input_amplitude = 3.14;
    float sine = sin(((float)addr-128.0)/128.0 * input_amplitude);
    fabric.chips[0].tiles[tileIndx].slices[sliceIndx].lut->setLut (
      addr,
      sine * 128.0 + 128
    );
    data[addr] = sine * 128.0 + 128;
    addr++;
  } while ( addr != 256 );

  // SRAM error-proof check
  fabric.chips[0].tiles[tileIndx].setParallelIn(true);
  fabric.chips[0].tiles[tileIndx].slices[sliceIndx].lut->setSource ( true, false, false );
  fabric.chips[0].tiles[tileIndx].slices[sliceIndx].lut->setParallelOut( true );
  fabric.cfgCommit();
  byte randAddr = 255;
  for (unsigned int checkIndx = 0; checkIndx < 256; checkIndx++) {
    fabric.chips[0].writeParallel(randAddr);
    unsigned char output = fabric.chips[0].readParallel();
    if (data[randAddr] != output) {
      Serial.print("addr=");
      Serial.print(randAddr);
      Serial.print(" ");
      Serial.print(data[randAddr]);
      Serial.print(" != ");
      Serial.println(output);
    }
    randAddr--;
  }
  // Disable the TDI/TDO channels
  fabric.chips[0].tiles[tileIndx].setParallelIn(false);

  /****ADC****/
  // connect something to the ADC input
  Fabric::Chip::Connection ( DAC_A->out0, fabric.chips[0].tiles[tileIndx].slices[sliceIndx].adc->in0 ).setConn();
  // turn on the ADC (optional, because connecting the ADC input also turns on ADC)
  fabric.chips[0].tiles[tileIndx].slices[sliceIndx].adc->setEnable ( true );



  /****LUT****/
  fabric.chips[0].tiles[tileIndx].slices[sliceIndx].lut->setSource (
    false, // lut takes input from chip parallel input
    false, // lut takes input from first analog to digital converter ******************************************************
    true // lut takes input from second analog to digital converter  ******************************************************
  );

  /****DAC****/
  // turn on the DAC (optional, because connecting the DAC output also turns on DAC)
  fabric.chips[0].tiles[tileIndx].slices[sliceIndx].dac->setEnable ( true );
  fabric.chips[0].tiles[tileIndx].slices[sliceIndx].dac->setSource (
    false, // digital to analog converter takes input from register
    false, // digital to analog converter takes input from chip parallel input
    false, // digital to analog converter takes input from first lookup table *********************************************
    true // digital to analog converter takes input from second lookup table  *********************************************
  );




  // connect something to the DAC output
  Fabric::Chip::Connection ( fabric.chips[0].tiles[tileIndx].slices[sliceIndx].dac->out0, tileout->in0 ).setConn();
  Fabric::Chip::Connection ( tileout->out0, fabric.chips[0].tiles[3].slices[2].chipOutput->in0 ).setConn();

//  DAC_A->setConstantCode(255);

  short value = 0;

  for (unsigned short rep = 0; rep < 65536; rep++) {
    for (value = 0; value < 256; value++) {
      fabric.chips[0].tiles[tileIndx].slices[sliceIndx].adc->setParallelOut( true );
      DAC_A->setConstantCode ( value );
    }
    for (value = 255; value > -1; value--) {
      DAC_A->setConstantCode ( value );
    }
  }

}

void loop () {}
