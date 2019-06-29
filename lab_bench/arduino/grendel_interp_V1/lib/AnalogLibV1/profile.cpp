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
    for(int i=10; i < 245; i += stride){
      data[idx] = (((float) i)/128.0 - 1.0);
      idx += 1;
    }
    return idx;
  }
  int data_2d(float* data,int size){
    static int codes[] = {10,32,64,96,128,
                          160,191,224,245};
    for(int i=0; i < 9; i += 1){
      data[i] = (codes[i]/128.0 - 1.0);
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
      sprintf(FMTBUF,
              "port=%s out=%f in0=%f in1=%f bias=%f noise=%f",
              result.port[i],
              float16::to_float32(result.target[i]),
              float16::to_float32(result.input0[i]),
              float16::to_float32(result.input1[i]),
              float16::to_float32(result.bias[i]),
              float16::to_float32(result.noise[i])
              );
      print_level(FMTBUF,level);
    }

  }
  void add_prop(profile_t& result,
                unsigned char prop,
                float target, float in0, float in1,
                float bias, float noise){
    if(result.size >= MAX_KEYS){
      sprintf(FMTBUF,
              "cutil::add_prop: no more space left for prop: %d/%d",
              result.size, MAX_KEYS);
      error(FMTBUF);
    }
    result.port[result.size] = prop;
    result.bias[result.size] = float16::from_float32(bias);
    result.noise[result.size] = float16::from_float32(noise);
    result.target[result.size] = float16::from_float32(target);
    result.input0[result.size] = float16::from_float32(in0);
    result.input1[result.size] = float16::from_float32(in1);
    sprintf(FMTBUF, "add-prop idx=%d prop=%d bias=%f noise=%f out=%f in0=%f in1=%f",
            result.size,prop,bias,noise,target,in0,in1);
    print_log(FMTBUF);
    result.size += 1;
  }



}
