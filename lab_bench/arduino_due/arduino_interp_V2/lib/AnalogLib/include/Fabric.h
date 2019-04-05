#ifndef FABRIC_H
#define FABRIC_H
#include "include/ProgIface.h"
#include "include/Block.h"

class Fabric {
	/*Connection specifies source FU interface and destination FU interface*/
 public:
  Fabric();
  ~Fabric();
  block_t block(BLOCK_TYPE block,unsigned char chip, unsigned char slice,
             unsigned char tile, unsigned char index);
  void reset();
  void prog_start();
  void prog_commit();
  void prog_done();
  void run_sim();
  void stop_sim();

  ProgIface * m_ifaces;
};

#endif

