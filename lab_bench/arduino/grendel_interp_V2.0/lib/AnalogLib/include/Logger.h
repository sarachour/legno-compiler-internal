#ifndef LOGGER_H
#define LOGGER_H

namespace logger {

void tag(const char * msg);
void print(const char * msg);
void print(int msg);
void newline();
void debug(const char * msg);
void warn(const char * msg);
void error(const char * msg);
void assert(bool assertion, const char * msg);

}
#endif
