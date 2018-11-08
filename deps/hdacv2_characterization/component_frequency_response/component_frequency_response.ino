#include <HCDC_DEMO_API.h>
#include <DueTimer.h>

const unsigned short buffSize = 1600;
// Precalculated DAC values.
uint16_t DAC_Array [buffSize + 1]; // last one is dummy

const float delayTimeMicroseconds = 50;
char HCDC_DEMO_BOARD = 5;
Fabric * fabric;

// Measured ADC values.
volatile uint16_t ADC_Array [buffSize + 1]; // first one is dummy
volatile unsigned short timeIndx = 0;

float adcCodeToVal (unsigned short adcCode) {
  return (3.267596063219 - 0.001592251629 * adcCode) / FULL_SCALE;
}

void setup() {
  SerialUSB.begin(1200);
  while (!SerialUSB);
  Timer3.attachInterrupt( myHandler );

  // Set up DAC
  analogWrite(DAC0, 2048);
  analogWrite(DAC1, 2048);
  dacc_set_transfer_mode(DACC_INTERFACE, 1); // 32 bit size transfer for writing both channels at once
  dacc_enable_flexible_selection (DACC_INTERFACE); // tagged mode for 32 bit transfer

  // Set up chip
  fabric = new Fabric();
  fabric->calibrate();
  fabric->chips[0].tiles[0].slices[0].muls[0].setGain( -0.1 );
}

void loop() {
  SerialUSB.print("tileIndx");
  SerialUSB.print("\t");
  SerialUSB.print("sliceIndx");
  SerialUSB.print("\t");
  SerialUSB.print("fuIndx");
  SerialUSB.print("\t");
  SerialUSB.print("freq");
  SerialUSB.print("\t");
  SerialUSB.print("samples");
  SerialUSB.print("\t");
  SerialUSB.print("amplitude");
  SerialUSB.print("\t");
  SerialUSB.println("phase");

  for (unsigned char tileIndx = 0; tileIndx < 1; tileIndx++) {
    for (unsigned char sliceIndx = 0; sliceIndx < 1; sliceIndx++) {
      for (unsigned char fuIndx = 0; fuIndx < 1; fuIndx++) {
        fabric->chips[0].tiles[tileIndx].slices[sliceIndx].integrator->setInitial(0.0);
        fabric->chips[0].tiles[tileIndx].slices[(sliceIndx + 2) % 4].integrator->setInitial(0.0);
        //        fabric->chips[0].tiles[tileIndx].slices[(sliceIndx + 2) % 4].integrator->out0->setInv(true);
        //        fabric->chips[0].tiles[tileIndx].slices[sliceIndx].muls[fuIndx].setGain( 0.25 );
        Fabric::Chip::Connection conn0 = Fabric::Chip::Connection ( fabric->chips[0].tiles[3].slices[3].chipInput->out0, fabric->chips[0].tiles[tileIndx].slices[sliceIndx].tileInps[2 * fuIndx].in0 );
        Fabric::Chip::Connection conn1 = Fabric::Chip::Connection ( fabric->chips[0].tiles[tileIndx].slices[sliceIndx].tileInps[2 * fuIndx].out0, fabric->chips[0].tiles[tileIndx].slices[sliceIndx].fans[fuIndx].in0 );
        Fabric::Chip::Connection conn2 = Fabric::Chip::Connection ( fabric->chips[0].tiles[tileIndx].slices[sliceIndx].fans[fuIndx].out0, fabric->chips[0].tiles[tileIndx].slices[sliceIndx].muls[fuIndx].in0 );
        Fabric::Chip::Connection conn4 = Fabric::Chip::Connection ( fabric->chips[0].tiles[tileIndx].slices[sliceIndx].muls[fuIndx].out0, fabric->chips[0].tiles[tileIndx].slices[(sliceIndx + 2) % 4].integrator->in0 );
        Fabric::Chip::Connection conn3 = Fabric::Chip::Connection ( fabric->chips[0].tiles[tileIndx].slices[(sliceIndx + 2) % 4].integrator->out0, fabric->chips[0].tiles[tileIndx].slices[sliceIndx].fans[fuIndx].in0 );
        Fabric::Chip::Connection conn5 = Fabric::Chip::Connection ( fabric->chips[0].tiles[tileIndx].slices[sliceIndx].fans[fuIndx].out1, fabric->chips[0].tiles[tileIndx].slices[sliceIndx].integrator->in0 );
        Fabric::Chip::Connection conn6 = Fabric::Chip::Connection ( fabric->chips[0].tiles[tileIndx].slices[sliceIndx].integrator->out0, fabric->chips[0].tiles[tileIndx].slices[sliceIndx].tileOuts[2 * fuIndx].in0 );
        Fabric::Chip::Connection conn7 = Fabric::Chip::Connection ( fabric->chips[0].tiles[tileIndx].slices[sliceIndx].tileOuts[2 * fuIndx].out0, fabric->chips[0].tiles[3].slices[2].chipOutput->in0 );
        conn0.setConn();
        conn1.setConn();
        conn2.setConn();
        conn3.setConn();
        conn4.setConn();
        conn5.setConn();
        conn6.setConn();
        conn7.setConn();
        fabric->cfgCommit();

        for ( float freq = 10; freq < 10000; freq *= 1.125 ) {
          float samples = 1000000.0 / freq / delayTimeMicroseconds;
          // t in radians
          for (timeIndx = 0; timeIndx < buffSize; timeIndx++) {
            DAC_Array[timeIndx] = sin(2.0 * PI * timeIndx / samples) * 2047.0 + 2048.0;
          }
          DAC_Array[buffSize] = 2048;

          timeIndx = 0;
          fabric->cfgStop();
          fabric->execStart();
          delay(2048);
          unsigned long startTime = micros();
          Timer3.start( delayTimeMicroseconds );
          while (timeIndx < buffSize) {};
          unsigned long endTime = micros();
          fabric->execStop();
          fabric->cfgStart();

          float mean = 0.0;
          for (timeIndx = 0; timeIndx < buffSize; timeIndx++) {
            //            SerialUSB.println(ADC_Array[timeIndx + 1]);
            mean += adcCodeToVal(ADC_Array[timeIndx + 1]);
          }
          mean /= (float)buffSize;

          float rms = 0.0;
          unsigned short negIndx = 0;
          for (timeIndx = 0; timeIndx < buffSize; timeIndx++) {
            float deviation = adcCodeToVal(ADC_Array[timeIndx + 1]) - mean;
            rms += deviation * deviation;
            if (negIndx == 0 && adcCodeToVal(ADC_Array[timeIndx + 1]) < mean) negIndx = timeIndx;
          }

          SerialUSB.print(tileIndx);
          SerialUSB.print("\t");
          SerialUSB.print(sliceIndx);
          SerialUSB.print("\t");
          SerialUSB.print(fuIndx);
          SerialUSB.print("\t");
          SerialUSB.print(freq);
          SerialUSB.print("\t");
          SerialUSB.print(samples);
          SerialUSB.print("\t");
          SerialUSB.print(sqrt(rms / (float)buffSize), 6);
          SerialUSB.print("\t");
          SerialUSB.println(((float)negIndx) / samples, 6);
        }

        conn0.brkConn();
        conn1.brkConn();
        conn2.brkConn();
        conn3.brkConn();
        conn4.brkConn();
        conn5.brkConn();
        conn6.brkConn();
        conn7.brkConn();
        fabric->cfgCommit();
      }
    }
  }
}

unsigned short binarySearch(
  unsigned short minCode,
  unsigned short maxCode
) {
  if (minCode == maxCode) return minCode;
  unsigned short avgCode = (minCode + maxCode) / 2;
  DACC->DACC_CDR = avgCode; // write on DAC
  fabric->cfgCommit();
  fabric->execStart();
  delay(1);
  float anaOut = fabric->chips[0].tiles[3].slices[2].chipOutput->analogAvg(255);
  fabric->execStop();
  if (anaOut < 0.0) {
    return binarySearch(avgCode, maxCode);
  } else {
    return binarySearch(minCode, avgCode);
  }
}

void myHandler() {
  ADC_Array[timeIndx] = ADC->ADC_CDR[6];
  DACC->DACC_CDR = (1 << 28) + (DAC_Array[timeIndx] << 16) + (0 << 12) + DAC_Array[timeIndx]; // tag, data, tag, data
  timeIndx++; if (timeIndx > buffSize) Timer3.stop();
}
