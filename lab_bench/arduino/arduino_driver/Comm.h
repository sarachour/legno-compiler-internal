#ifndef COMM_H
#define COMM_H
#include <Arduino.h>


void read_bytes(uint8_t * data, int n);
void read_floats(float * data, int n);
uint8_t read_byte();
#endif 
