#ifndef COMM_H
#define COMM_H
#include <Arduino.h>

void* get_data_ptr(int offset);
int read_bytes(uint8_t * data, int n);
int read_floats(float * data, int n);
uint8_t read_byte();
void discard_bytes(int n);
void listen();
bool read_mode();
void reset();
int write_pos();
#endif 
