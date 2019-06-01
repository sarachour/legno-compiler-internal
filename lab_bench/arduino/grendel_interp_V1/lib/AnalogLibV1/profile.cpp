#include "profile.h"
#include "AnalogLib.h"

namespace prof {

  profile_t TEMP;

  int size_1d(){
    return SIZE1D;
  }
  int size_2d(){
    return SIZE2D;
  }
  int data_1d(float* data,int size){
    unsigned int stride = 5;
    if(size < 51){
      error("not enough space to allocate data");
    }
    int idx = 0;
    for(int i=0; i < 256; i += stride){
      data[idx] = ((float) i)/128.0 - 1.0;
      idx += 1;
    }
    return idx;
  }
  int data_2d(float* data,int size){
    static int codes[] = {0,32,64,96,128,
                          160,191,224,255};
    for(int i=0; i < 9; i += 1){
      data[i] = codes[i]/128.0 - 1.0;
    }
    return 9;
  }

 void init_profile(profile_t& result){
    result.size = 0;
    for(int i=0; i < MAX_KEYS; i += 1){
      result.port[i] = 0;
      result.noise[i] = 0.0;
      result.bias[i] = 0.0;
      result.target[i] = 0.0;
    }
  }

  void print_profile(profile_t& result, int level){
    for(int i=0; i < result.size; i+= 1){
      sprintf("port=%s target=%f bias=%f noise=%f", result.port[i],
              result.target[i],result.bias[i],result.noise[i]);
      print_level(FMTBUF,level);
    }

  }
  void add_prop(profile_t& result,
                unsigned char prop, float target, float bias, float noise){
    if(result.size >= MAX_KEYS){
      sprintf(FMTBUF,
              "cutil::add_prop: no more space left for prop: %d/%d",
              result.size, MAX_KEYS);
      error(FMTBUF);
    }
    result.port[result.size] = prop;
    result.bias[result.size] = bias;
    result.noise[result.size] = noise;
    result.target[result.size] = target;
    sprintf(FMTBUF, "add-prop prop=%d bias=%f noise=%f target=%f",
            prop,bias,noise,target);
    print_log(FMTBUF);
    result.size += 1;
  }



}
