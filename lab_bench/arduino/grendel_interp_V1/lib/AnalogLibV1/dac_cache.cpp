#include "AnalogLib.h"
#include "dac.h"

dac_cache_t DAC_CACHE;

namespace dac_cache {



  void initialize(){
    for(int i=0; i < NCACHE_SLOTS; i++){
      DAC_CACHE.owners[i] = NULL;
      DAC_CACHE.lru_dac[i] = 0;
      for(int j=0; j < NCACHE_ELS; j+=1){
        DAC_CACHE.is_cached[i][j] = false;
        DAC_CACHE.lru_val[i][j] = 0;
      }
    }

  }
  int oldest_row(){
    int oldest_row = 0;
    for(int i=0; i < NCACHE_SLOTS; i+=1){
      if(DAC_CACHE.lru_dac[i] > DAC_CACHE.lru_dac[oldest_row]){
        oldest_row = i;
      }
    }
    print_log(FMTBUF);
    return oldest_row;
  }
  int oldest_cell(int row){
    int best_cell = 0;
    for(int i=0; i < NCACHE_ELS; i += 1){
      if(DAC_CACHE.lru_val[row][i] > DAC_CACHE.lru_val[row][best_cell]){
        best_cell = i;
      }
    }
    return best_cell;
  }
  void age(){
    for(int i=0; i < NCACHE_SLOTS; i+=1){
      DAC_CACHE.lru_dac[i] += 1;
      for(int j=0; j < NCACHE_ELS; j += 1){
        DAC_CACHE.lru_val[i][j] += 1;
      }
    }
  }
  void use(int line, int cell){
    DAC_CACHE.lru_dac[line] = 0;
    DAC_CACHE.lru_val[line][cell] = 0;
  }

  int new_line(Fabric::Chip::Tile::Slice::Dac* dac){
    int slot = oldest_row();
    for(int i=0; i < NCACHE_ELS; i+=1){
      DAC_CACHE.is_cached[slot][i] = false;
      DAC_CACHE.lru_val[slot][i] = 0;
    }
    DAC_CACHE.owners[slot] = dac;
    DAC_CACHE.lru_dac[slot] = 0;
    return slot;
  }
  int new_cell(Fabric::Chip::Tile::Slice::Dac* dac,int line){
    int cell = oldest_cell(line);
    DAC_CACHE.is_cached[line][cell] = false;
    DAC_CACHE.lru_val[line][cell] = 0;
    return cell;
  }
  int get_line(Fabric::Chip::Tile::Slice::Dac* dac){
    for(int i=0; i < NCACHE_SLOTS; i += 1){
      if(DAC_CACHE.owners[i] == dac){
        return i;
      }
    }
    return new_line(dac);
  }
  bool get_cell(Fabric::Chip::Tile::Slice::Dac* dac,
                float value,
                int& line,
                int& cell){
    int slot = get_line(dac);
    line = slot;

    for(int i = 0; i < NCACHE_ELS; i += 1){
      float cached_value = DAC_CACHE.cache[slot][i].const_val;
      if(fabs(value - cached_value) < 1e-3 &&
         DAC_CACHE.is_cached[slot][i]){
        cell = i;
        return true;
      }
    }
    cell = new_cell(dac,slot);
    return false;
  }
  bool get_cached(Fabric::Chip::Tile::Slice::Dac* dac,
                  float value,
                  dac_code_t& this_code){
    int line,cell;
    bool in_cache = get_cell(dac,value,line,cell);
    if(in_cache){
      use(line,cell);
      this_code = DAC_CACHE.cache[line][cell];
    }
    return in_cache;
  }

  void cache(Fabric::Chip::Tile::Slice::Dac* dac,
             float value,
             dac_code_t& this_code){
    int line,cell;
    bool is_cached = get_cell(dac,value,line,cell);
    DAC_CACHE.cache[line][cell] = this_code;
    age();
    use(line,cell);
    DAC_CACHE.lru_dac[line] = 0;
    DAC_CACHE.lru_val[line][cell] = 0;

  }
}
