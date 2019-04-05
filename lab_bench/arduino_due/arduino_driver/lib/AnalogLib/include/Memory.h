#ifndef MEMORY_H
#define MEMORY_H
extern size_t dynamic_memory;

template <typename type>
void tally_dyn_mem(
                   const char * name
                   ) {
	dynamic_memory += sizeof(type);
}

#endif
