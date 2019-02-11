#define _DUE
#include <HCDC_DEMO_API.h>
#include "complex_mult/ComplexMult.h"
#include "ComplexDiv.h"
#include "TestTile.h"
#include "TestChip.h"

Fabric * fabric;
unsigned char HCDC_DEMO_BOARD = 1;
float probRange = 2.0;

// test the complex number square division n/d
void setup() {
  fabric = new Fabric();
  fabric->calibrate();
  Serial.println("numer_real\tnumer_imag\tdenom_real\tdenom_imag\tctrl_real\tctrl_imag\texpr_real\texpr_imag");
}

void loop () {
  for (unsigned char chipIndx = 0; chipIndx < 2; chipIndx++) {
    for (unsigned char tileIndx = 0; tileIndx < 4; tileIndx++) {

      TestChip testChip = TestChip (
        fabric->chips[chipIndx].tiles[tileIndx],
        fabric->chips[chipIndx].tiles[(tileIndx+1)%4]
      );

      // mult outputs
      Fabric::Chip::Connection quoti_real_conn = Fabric::Chip::Connection ( testChip.quoti_chip_real_out, fabric->chips[chipIndx].tiles[3].slices[2].chipOutput->in0 );
      Fabric::Chip::Connection quoti_imag_conn = Fabric::Chip::Connection ( testChip.quoti_chip_imag_out, fabric->chips[chipIndx].tiles[3].slices[3].chipOutput->in0 );
      quoti_real_conn.setConn(); quoti_imag_conn.setConn();

      float nr = -probRange + (float)(rand()) / (float)(RAND_MAX / (probRange - (-probRange)));
      float ni = -probRange + (float)(rand()) / (float)(RAND_MAX / (probRange - (-probRange)));
      float dr = -probRange + (float)(rand()) / (float)(RAND_MAX / (probRange - (-probRange)));
      float di = -probRange + (float)(rand()) / (float)(RAND_MAX / (probRange - (-probRange)));

      Serial.print( nr, 6 ); Serial.print('\t');
      Serial.print( ni, 6 ); Serial.print('\t');
      Serial.print( dr, 6 ); Serial.print('\t');
      Serial.print( di, 6 ); Serial.print('\t');
      Serial.print( (nr*dr+ni*di)/(dr*dr+di*di), 6 ); Serial.print('\t'); // complex division using conjugates
      Serial.print( (ni*dr-nr*di)/(dr*dr+di*di), 6 ); Serial.print('\t'); // complex division using conjugates

      testChip.setXY ( nr, ni, dr, di );

      fabric->cfgCommit();
      fabric->execStart();
      float qr = fabric->chips[chipIndx].tiles[3].slices[2].chipOutput->analogAvg(CAL_REPS) / FULL_SCALE;
      float qi = fabric->chips[chipIndx].tiles[3].slices[3].chipOutput->analogAvg(CAL_REPS) / FULL_SCALE;
      fabric->execStop();
      Serial.print(-qr, 6); Serial.print('\t');
      Serial.print(-qi, 6); Serial.println('\t');

      quoti_real_conn.brkConn(); quoti_imag_conn.brkConn();
    }
  }
}
