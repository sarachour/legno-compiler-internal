#define _DUE
#include <HCDC_DEMO_API.h>

Fabric * fabric;

void setup() {
  fabric = new Fabric();

  pinMode(26, OUTPUT);
  pinMode(27, OUTPUT);
  pinMode(28, OUTPUT);
  pinMode(29, OUTPUT);

  digitalWrite(26, LOW);
  digitalWrite(27, LOW);
  digitalWrite(28, LOW);
  digitalWrite(29, HIGH);

  // directly connect input to output
  Fabric::Chip::Connection conn0 ( fabric->chips[0].tiles[3].slices[2].chipInput->out0, fabric->chips[0].tiles[3].slices[2].chipOutput->in0 );
  Fabric::Chip::Connection conn1 ( fabric->chips[0].tiles[3].slices[3].chipInput->out0, fabric->chips[0].tiles[3].slices[3].chipOutput->in0 );
  Fabric::Chip::Connection conn2 ( fabric->chips[1].tiles[3].slices[2].chipInput->out0, fabric->chips[1].tiles[3].slices[2].chipOutput->in0 );
  Fabric::Chip::Connection conn3 ( fabric->chips[1].tiles[3].slices[3].chipInput->out0, fabric->chips[1].tiles[3].slices[3].chipOutput->in0 );

  conn0.setConn();
  conn1.setConn();
  conn2.setConn();
  conn3.setConn();

  fabric->cfgCommit();
}

void loop () {}
