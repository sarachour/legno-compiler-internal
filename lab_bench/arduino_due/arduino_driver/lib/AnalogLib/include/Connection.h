
typedef struct CONNECTION {
  block_t src;
  block_t dst;
} conn_t;

conn_t mkconn(block_t& b1,PORT p1, block_t& b2, PORT p2);
conn_t brkconn(block_t& b1,PORT p1, block_t& b2, PORT p2);
