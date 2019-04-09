#ifndef CONNECTION_H
#define CONNECTION_H

#include "include/Block.h"

namespace conn {
void mkconn(block_t& b1,PORT_NAME p1, block_t& b2, PORT_NAME p2);
void brkconn(block_t& b1,PORT_NAME p1, block_t& b2, PORT_NAME p2);
}

#endif
