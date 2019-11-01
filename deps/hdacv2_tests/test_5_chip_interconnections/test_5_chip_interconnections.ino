#define _DUE
#include <HCDC_DEMO_API.h>

Fabric * fabric;

void setup() {

  pinMode(26, OUTPUT);
  pinMode(27, OUTPUT);
  pinMode(28, OUTPUT);
  pinMode(29, OUTPUT);

  digitalWrite(26, LOW);
  digitalWrite(27, LOW);
  digitalWrite(28, LOW);
  digitalWrite(29, LOW);

  
  fabric = new Fabric();
  tally_dyn_mem <Fabric> ("Fabric");

  Serial.print ("dynamic_memory = ");
  Serial.println (dynamic_memory);

  // weave back and forth
  Fabric::Chip::Connection conn00 ( fabric->chips[0].tiles[0].slices[0].dac->out0, fabric->chips[0].tiles[0].slices[0].tileOuts[0].in0 );

  // tile 0.0.0.0 -> 0.0.0.0
  // 0.0.0 -> 1.1.3
  Fabric::Chip::Connection conn01 ( fabric->chips[0].tiles[0].slices[0].tileOuts[0].out0, fabric->chips[0].tiles[0].slices[0].chipOutput->in0 );
  // 1.0.0 -> 0.1.3
  Fabric::Chip::Connection conn02 ( fabric->chips[1].tiles[1].slices[3].chipInput->out0, fabric->chips[1].tiles[0].slices[0].chipOutput->in0 );
  Fabric::Chip::Connection conn03 ( fabric->chips[0].tiles[1].slices[3].chipInput->out0, fabric->chips[0].tiles[0].slices[1].chipOutput->in0 );
  Fabric::Chip::Connection conn04 ( fabric->chips[1].tiles[1].slices[2].chipInput->out0, fabric->chips[1].tiles[0].slices[1].chipOutput->in0 );
  Fabric::Chip::Connection conn05 ( fabric->chips[0].tiles[1].slices[2].chipInput->out0, fabric->chips[0].tiles[0].slices[2].chipOutput->in0 );
  Fabric::Chip::Connection conn06 ( fabric->chips[1].tiles[1].slices[1].chipInput->out0, fabric->chips[1].tiles[0].slices[2].chipOutput->in0 );
  Fabric::Chip::Connection conn07 ( fabric->chips[0].tiles[1].slices[1].chipInput->out0, fabric->chips[0].tiles[0].slices[3].chipOutput->in0 );
  Fabric::Chip::Connection conn08 ( fabric->chips[1].tiles[1].slices[0].chipInput->out0, fabric->chips[1].tiles[0].slices[3].chipOutput->in0 );
  Fabric::Chip::Connection conn09 ( fabric->chips[0].tiles[1].slices[0].chipInput->out0, fabric->chips[0].tiles[1].slices[0].chipOutput->in0 );
  Fabric::Chip::Connection conn10 ( fabric->chips[1].tiles[2].slices[3].chipInput->out0, fabric->chips[1].tiles[1].slices[0].chipOutput->in0 );
  Fabric::Chip::Connection conn11 ( fabric->chips[0].tiles[2].slices[3].chipInput->out0, fabric->chips[0].tiles[1].slices[1].chipOutput->in0 );
  Fabric::Chip::Connection conn12 ( fabric->chips[1].tiles[2].slices[2].chipInput->out0, fabric->chips[1].tiles[1].slices[1].chipOutput->in0 );
  Fabric::Chip::Connection conn13 ( fabric->chips[0].tiles[2].slices[2].chipInput->out0, fabric->chips[0].tiles[1].slices[2].chipOutput->in0 );
  Fabric::Chip::Connection conn14 ( fabric->chips[1].tiles[2].slices[1].chipInput->out0, fabric->chips[1].tiles[1].slices[2].chipOutput->in0 );
  Fabric::Chip::Connection conn15 ( fabric->chips[0].tiles[2].slices[1].chipInput->out0, fabric->chips[0].tiles[1].slices[3].chipOutput->in0 );
  Fabric::Chip::Connection conn16 ( fabric->chips[1].tiles[2].slices[0].chipInput->out0, fabric->chips[1].tiles[1].slices[3].chipOutput->in0 );
  Fabric::Chip::Connection conn17 ( fabric->chips[0].tiles[2].slices[0].chipInput->out0, fabric->chips[0].tiles[2].slices[0].chipOutput->in0 );
  Fabric::Chip::Connection conn18 ( fabric->chips[1].tiles[0].slices[3].chipInput->out0, fabric->chips[1].tiles[2].slices[0].chipOutput->in0 );
  Fabric::Chip::Connection conn19 ( fabric->chips[0].tiles[0].slices[3].chipInput->out0, fabric->chips[0].tiles[2].slices[1].chipOutput->in0 );
  Fabric::Chip::Connection conn20 ( fabric->chips[1].tiles[0].slices[2].chipInput->out0, fabric->chips[1].tiles[2].slices[1].chipOutput->in0 );
  Fabric::Chip::Connection conn21 ( fabric->chips[0].tiles[0].slices[2].chipInput->out0, fabric->chips[0].tiles[2].slices[2].chipOutput->in0 );
  Fabric::Chip::Connection conn22 ( fabric->chips[1].tiles[0].slices[1].chipInput->out0, fabric->chips[1].tiles[2].slices[2].chipOutput->in0 );
  Fabric::Chip::Connection conn23 ( fabric->chips[0].tiles[0].slices[1].chipInput->out0, fabric->chips[0].tiles[2].slices[3].chipOutput->in0 );
  Fabric::Chip::Connection conn24 ( fabric->chips[1].tiles[0].slices[0].chipInput->out0, fabric->chips[1].tiles[2].slices[3].chipOutput->in0 );
  Fabric::Chip::Connection conn25 ( fabric->chips[0].tiles[0].slices[0].chipInput->out0, fabric->chips[0].tiles[3].slices[0].chipOutput->in0 );
  Fabric::Chip::Connection conn26 ( fabric->chips[1].tiles[3].slices[0].chipInput->out0, fabric->chips[1].tiles[3].slices[0].chipOutput->in0 );
  Fabric::Chip::Connection conn27 ( fabric->chips[0].tiles[3].slices[0].chipInput->out0, fabric->chips[0].tiles[3].slices[1].chipOutput->in0 );
  Fabric::Chip::Connection conn28 ( fabric->chips[1].tiles[3].slices[1].chipInput->out0, fabric->chips[1].tiles[3].slices[1].chipOutput->in0 );
  Fabric::Chip::Connection conn29 ( fabric->chips[0].tiles[3].slices[1].chipInput->out0, fabric->chips[0].tiles[3].slices[3].chipOutput->in0 );


  conn00.setConn();
  conn01.setConn();
  conn02.setConn();
  conn03.setConn();
  conn04.setConn();
  conn05.setConn();
  conn06.setConn();
  conn07.setConn();
  conn08.setConn();
  conn09.setConn();
  conn10.setConn();
  conn11.setConn();
  conn12.setConn();
  conn13.setConn();
  conn14.setConn();
  conn15.setConn();
  conn16.setConn();
  conn17.setConn();
  conn18.setConn();
  conn19.setConn();
  conn20.setConn();
  conn21.setConn();
  conn22.setConn();
  conn23.setConn();
  conn24.setConn();
  conn25.setConn();
  conn26.setConn();
  conn27.setConn();
  conn28.setConn();
  conn29.setConn();

  fabric->cfgCommit();
}

void loop () {
  for (unsigned short val = 0; val < 256; val++) {
    fabric->chips[0].tiles[0].slices[0].dac->setConstantCode(val);
    Serial.println(fabric->chips[0].tiles[3].slices[3].chipOutput->analogAvg(2));
  }
}
