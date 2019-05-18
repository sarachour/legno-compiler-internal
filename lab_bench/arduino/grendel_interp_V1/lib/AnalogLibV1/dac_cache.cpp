#include "AnalogLib.h"
#include "dac.h"

dac_cache_t DAC_CACHE;

namespace dac_cache {


  const float VALUES[NCACHE_ELS] = {-9,-7,-5,-3,-1,
                                    1,3,5,7,9};


  void initialize(){
    for(int i=0; i < NCACHE_SLOTS; i++){
      DAC_CACHE.owners[i] = NULL;
      DAC_CACHE.lru[i] = 0;
      for(int j=0; j < NCACHE_ELS; j+=1){
        DAC_CACHE.is_cached[i][j] = false;
      }
    }

  }
  int oldest_row(){
    int oldest_row = 0;
    for(int i=0; i < NCACHE_SLOTS; i+=1){
      if(DAC_CACHE.lru[i] > DAC_CACHE.lru[oldest_row]){
        oldest_row = i;
      }
    }
    print_log(FMTBUF);
    return oldest_row;
  }
  void age(){
    for(int i=0; i < NCACHE_SLOTS; i+=1){
      DAC_CACHE.lru[i] += 1;
    }
  }
  int new_line(Fabric::Chip::Tile::Slice::Dac* dac){
    int slot = oldest_row();
    for(int i=0; i < NCACHE_ELS; i+=1){
      DAC_CACHE.is_cached[slot][i] = false;
    }
    DAC_CACHE.owners[slot] = dac;
    age();
    DAC_CACHE.lru[slot] = 0;
    return slot;
  }
  int get_line(Fabric::Chip::Tile::Slice::Dac* dac){
    for(int i=0; i < NCACHE_SLOTS; i += 1){
      if(DAC_CACHE.owners[i] == dac){
        age();
        DAC_CACHE.lru[i] = 0;
        print_log(FMTBUF);
        return i;
      }
    }
    return new_line(dac);
  }
  bool get_cached(Fabric::Chip::Tile::Slice::Dac* dac,
                  float value,
                  dac_code_t& this_code){
    int slot = get_line(dac);
    for(int i = 0; i < NCACHE_ELS; i += 1){
      if(fabs(value - VALUES[i]) < 1e-3 &&
         DAC_CACHE.is_cached[slot][i]){
        this_code = DAC_CACHE.cache[slot][i];
        sprintf(FMTBUF, "found code slot=%d idx=%d", slot, i);
        print_log(FMTBUF);
        return true;
      }
    }
    return false;
  }

  void cache(Fabric::Chip::Tile::Slice::Dac* dac,
             float value,
             dac_code_t& this_code){
    int slot = get_line(dac);
    for(int i = 0; i < NCACHE_ELS; i += 1){
      if(fabs(value - VALUES[i]) < 1e-3){
        DAC_CACHE.is_cached[slot][i] = true;
        DAC_CACHE.cache[slot][i] = this_code;
        sprintf(FMTBUF, "update code slot=%d idx=%d", slot, i);
        print_log(FMTBUF);
      }
    }
  }
}
