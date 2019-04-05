#include "include/Fabric.h"
#include "include/Pin.h"
#include "include/ProgIface.h"

Fabric::Fabric () {
	/*SPI PINS*/
  setup_pins();
  setup_io();
  /*scan chain disable*/
  pin_reset();
}

void Fabric::prog_commit(){
}

void Fabric::prog_start(){
}

void Fabric::prog_done(){
}

void Fabric::run_sim(){
}
void Fabric::stop_sim(){
}
