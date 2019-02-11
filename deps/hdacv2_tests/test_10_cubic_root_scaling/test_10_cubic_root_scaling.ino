#define _DUE
#include <HCDC_DEMO_API.h>
#include "complex_square/ComplexSquare.h"
#include "Jacobian.h"
#include "complex_mult_scaling/ComplexMultScaling.h"
#include "Function.h"
#include "complex_div/complex_mult/ComplexMult.h"
#include "complex_div/ComplexDiv.h"
#include "ContinNewton.h"
#include "NewtonChip.h"

Fabric * fabric;
NewtonChip * newton;
unsigned char HCDC_DEMO_BOARD = 1;
float biasRange = 2.0;
float initRange = 2.0;

// find the three complex roots of x^3+CONST=0
void setup() {

  fabric = new Fabric();
  fabric->calibrate();
  newton = new NewtonChip ( fabric->chips[0], biasRange, 0.0, 0.0, 0.0, 0.0 );

  float bias_real = 1.0; // -biasRange + (float)(rand()) / (float)(RAND_MAX / (biasRange - (-biasRange)));
  float bias_imag = 0.0; // -biasRange + (float)(rand()) / (float)(RAND_MAX / (biasRange - (-biasRange)));
  newton->setBias ( biasRange, bias_real, bias_imag );

  // x outputs
  Fabric::Chip::Connection x_real_conn = Fabric::Chip::Connection ( newton->x_chip_real_out, fabric->chips[0].tiles[3].slices[2].chipOutput->in0 );
  Fabric::Chip::Connection x_imag_conn = Fabric::Chip::Connection ( newton->x_chip_imag_out, fabric->chips[0].tiles[3].slices[3].chipOutput->in0 );
  x_real_conn.setConn(); x_imag_conn.setConn();

  //  Serial.println("bias_real\tbias_imag\tinit_real\tinit_imag\tfinal_real\tfinal_imag\tfunct_real\tfunct_imag");
  Serial.println("init_real\tinit_imag\tfinal_real\tfinal_imag\tfunct_real\tfunct_imag");

  //      init_real = -initRange + (float)(rand()) / (float)(RAND_MAX / (initRange - (-initRange)));
  //      init_imag = -initRange + (float)(rand()) / (float)(RAND_MAX / (initRange - (-initRange)));
  for ( float init_real = -initRange ; init_real < initRange ; init_real += initRange / 16 ) { // div by 32 leads to 64x64 image
    newton->setInitialReal ( biasRange, init_real );

    for ( float init_imag = -initRange ; init_imag < initRange ; init_imag += initRange / 16 ) { // div by 32 leads to 64x64 image
      newton->setInitialImag ( biasRange, init_imag );

      fabric->cfgCommit();
      fabric->execStart();
      //      delay(4);
      Serial.print( init_real, 6 ); Serial.print('\t');
      Serial.print( init_imag, 6 ); Serial.print('\t');
      float fr = fabric->chips[0].tiles[3].slices[2].chipOutput->analogAvg(CAL_REPS) * biasRange / FULL_SCALE;
      float fi = fabric->chips[0].tiles[3].slices[3].chipOutput->analogAvg(CAL_REPS) * biasRange / FULL_SCALE;
      fabric->execStop();

      //      Serial.print( bias_real, 6 ); Serial.print('\t');
      //      Serial.print( bias_imag, 6 ); Serial.print('\t');
      Serial.print(fr, 6); Serial.print('\t');
      Serial.print(fi, 6); Serial.print('\t');
      Serial.print(fr * fr * fr - 3 * fr * fi * fi + bias_real, 6); Serial.print('\t');
      Serial.print(3 * fr * fr * fi - fi * fi * fi + bias_imag, 6); Serial.println('\t');

    }
  }

  //  x_real_conn.brkConn(); x_imag_conn.brkConn();
  //  delete newton;
  //  delete fabric;

}

void loop () {}
