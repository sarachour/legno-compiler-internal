#define _DUE
#include <HCDC_DEMO_API.h>
#include "ComplexMult.h"
#include "TestTile.h"

Fabric * fabric;
char HCDC_DEMO_BOARD = 1;
float probRange = -1.0;

// test the complex number square mult
void setup() {
  fabric = new Fabric();
  fabric->calibrate();
  Serial.println("xinp_real\txinp_imag\tyinp_real\tyinp_imag\tctrl_real\tctrl_imag\texpr_real\texpr_imag");
}

void loop () {
  for (unsigned char chipIndx = 0; chipIndx < 2; chipIndx++) {
    for (unsigned char tileIndx = 0; tileIndx < 4; tileIndx++) {
      TestTile testTile = TestTile ( fabric->chips[chipIndx].tiles[tileIndx] );

      // mult outputs
      Fabric::Chip::Connection mult_real_conn = Fabric::Chip::Connection ( testTile.mult_real_out, fabric->chips[chipIndx].tiles[3].slices[2].chipOutput->in0 );
      Fabric::Chip::Connection mult_imag_conn = Fabric::Chip::Connection ( testTile.mult_imag_out, fabric->chips[chipIndx].tiles[3].slices[3].chipOutput->in0 );
      mult_real_conn.setConn(); mult_imag_conn.setConn();

      float xr = -probRange + (float)(rand()) / (float)(RAND_MAX / (probRange - (-probRange)));
      float xi = -probRange + (float)(rand()) / (float)(RAND_MAX / (probRange - (-probRange)));
      float yr = -probRange + (float)(rand()) / (float)(RAND_MAX / (probRange - (-probRange)));
      float yi = -probRange + (float)(rand()) / (float)(RAND_MAX / (probRange - (-probRange)));

      Serial.print( xr, 6 ); Serial.print('\t');
      Serial.print( xi, 6 ); Serial.print('\t');
      Serial.print( yr, 6 ); Serial.print('\t');
      Serial.print( yi, 6 ); Serial.print('\t');
      Serial.print( xr * yr - xi * yi, 6 ); Serial.print('\t');
      Serial.print( xr * yi + xi * yr, 6 ); Serial.print('\t');

      testTile.setXY ( xr, xi, yr, yi );

      fabric->cfgCommit();
      float mr = fabric->chips[chipIndx].tiles[3].slices[2].chipOutput->analogAvg(CAL_REPS) / FULL_SCALE;
      float mi = fabric->chips[chipIndx].tiles[3].slices[3].chipOutput->analogAvg(CAL_REPS) / FULL_SCALE;
      Serial.print(mr, 6); Serial.print('\t');
      Serial.print(mi, 6); Serial.println('\t');

      mult_real_conn.brkConn(); mult_imag_conn.brkConn();
    }
  }
}
