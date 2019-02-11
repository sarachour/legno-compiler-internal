#define _DUE
#include <HCDC_DEMO_API.h>
#include "ComplexSquare.h"
#include "TestTile.h"

Fabric * fabric;
unsigned char HCDC_DEMO_BOARD = 1;
float probRange = 2.0;

// test the complex number square mult
void setup() {
  fabric = new Fabric();
  fabric->calibrate();
  Serial.println("xinp_real\txinp_imag\tctrl_real\tctrl_imag\texpr_real\texpr_imag");
}

void loop () {
  for (unsigned char chipIndx = 0; chipIndx < 2; chipIndx++) {
    for (unsigned char tileIndx = 0; tileIndx < 4; tileIndx++) {

      TestTile testTile = TestTile ( fabric->chips[chipIndx].tiles[tileIndx] );

      // square outputs
      Fabric::Chip::Connection sq_real_conn = Fabric::Chip::Connection ( testTile.sq_real_out, fabric->chips[chipIndx].tiles[3].slices[2].chipOutput->in0 );
      Fabric::Chip::Connection sq_imag_conn = Fabric::Chip::Connection ( testTile.sq_imag_out, fabric->chips[chipIndx].tiles[3].slices[3].chipOutput->in0 );
      sq_real_conn.setConn(); sq_imag_conn.setConn();

      float xr = -probRange + (float)(rand()) / (float)(RAND_MAX / (probRange - (-probRange)));
      float xi = -probRange + (float)(rand()) / (float)(RAND_MAX / (probRange - (-probRange)));
      Serial.print( xr, 6 ); Serial.print('\t');
      Serial.print( xi, 6 ); Serial.print('\t');
      Serial.print( xr * xr - xi * xi, 6 ); Serial.print('\t');
      Serial.print( 2 * xr * xi, 6 ); Serial.print('\t');
      testTile.setX ( xr, xi );

      fabric->cfgCommit();
      float sr = fabric->chips[chipIndx].tiles[3].slices[2].chipOutput->analogAvg(CAL_REPS) / FULL_SCALE;
      float si = fabric->chips[chipIndx].tiles[3].slices[3].chipOutput->analogAvg(CAL_REPS) / FULL_SCALE;
      Serial.print(sr, 6); Serial.print('\t');
      Serial.print(si, 6); Serial.println('\t');

      sq_real_conn.brkConn(); sq_imag_conn.brkConn();
    }
  }
}
