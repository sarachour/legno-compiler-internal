#include "profile.h"
#include "AnalogLib.h"

namespace prof {

  profile_t TEMP;

  void print_profile(profile_t& result, int level){
    sprintf(FMTBUF,
            "port=%s mode=%d out=%f in0=%f in1=%f bias=%f noise=%f",
            result.port,
            result.mode,
            float16::to_float32(result.target),
            float16::to_float32(result.input0),
            float16::to_float32(result.input1),
            float16::to_float32(result.bias),
            float16::to_float32(result.noise)
            );

  }
  profile_t make_profile(unsigned char prop,
                    unsigned char mode,
                    float target, float in0, float in1,
                    float bias, float noise){
    profile_t result;
    result.port = prop;
    result.mode = mode;
    result.bias = float16::from_float32(bias);
    result.noise = float16::from_float32(noise);
    result.target = float16::from_float32(target);
    result.input0 = float16::from_float32(in0);
    result.input1 = float16::from_float32(in1);
    sprintf(FMTBUF, "prof idx=%d prop=%d bias=%f noise=%f out=%f in0=%f in1=%f",
            result.size,prop,bias,noise,target,in0,in1);
    print_log(FMTBUF);
    return result;
  }



}
