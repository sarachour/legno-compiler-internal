#ifndef FABRIC_H
#define FABRIC_H

class Fabric {
	/*Connection specifies source FU interface and destination FU interface*/
 public:
  Fabric();
  ~Fabric();
  void reset();
  void prog_start();
  void prog_commit();
  void prog_done();
  void run_sim();
  void stop_sim();

};

#endif

