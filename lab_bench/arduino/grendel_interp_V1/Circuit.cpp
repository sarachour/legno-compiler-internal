//#define _DUE
#include "AnalogLib.h"
#include "Circuit.h"
#include "Comm.h"
#include <assert.h>

char HCDC_DEMO_BOARD = 6;
//char HCDC_DEMO_BOARD = 4;


namespace circ {

bool caltbl[2][4][4];


void init_calibrations(){
  for(int chipno=0; chipno < 2; chipno ++){
    for(int tileno = 0; tileno < 4; tileno ++){
      for(int sliceno = 0; sliceno < 4; sliceno ++){
        caltbl[chipno][tileno][sliceno] = false;
      }
    }
  }
}

bool do_calibrate(int chipno, int tileno, int sliceno){
  if(not caltbl[chipno][tileno][sliceno]){
    caltbl[chipno][tileno][sliceno] = true;
    return true;
  }
  else{
    comm::print_header();
    Serial.println("-> skipping calibration");
    return false;
  }
}
Fabric::Chip::Tile::Slice* get_slice(Fabric * fab, circ_loc_t& loc){
  return &fab->chips[loc.chip].tiles[loc.tile].slices[loc.slice];
}

Fabric::Chip::Tile::Slice::Multiplier* get_mult(Fabric * fab, circ_loc_idx1_t& loc){
  Fabric::Chip::Tile::Slice::Multiplier * mult; 
  Fabric::Chip::Tile::Slice * slice = get_slice(fab,loc.loc);
  switch(loc.idx){
     case 0:
        mult = &slice->muls[0];
        break;
     case 1:
        mult = &slice->muls[1];
        break;
     default:
       comm::error("unknown multiplier index (not 0 or 1).");
       break;
  }
  return mult;
}

Fabric::Chip::Tile::Slice::Fanout* get_fanout(Fabric * fab, circ_loc_idx1_t& loc){
  Fabric::Chip::Tile::Slice::Fanout * fanout;
  Fabric::Chip::Tile::Slice * slice = get_slice(fab,loc.loc);
  switch(loc.idx){
     case 0:
        fanout = &slice->fans[0];
        break;
     case 1:
        fanout = &slice->fans[1];
        break;
     default:
       comm::error("unknown fanout index (not 0 or 1).");
       break;
  }
  return fanout;
}

Fabric::Chip::Tile::Slice::FunctionUnit::Interface* get_input_port(Fabric * fab, uint16_t& btype, circ_loc_idx2_t& loc){
  switch(btype){
    case TILE_DAC:
      comm::error("dac has no input port");
      break;

    case TILE_ADC:
      return get_slice(fab,loc.idxloc.loc)->adc->in0;
      break;

    case MULT:
       switch(loc.idx2){
         case 0:
           return get_mult(fab,loc.idxloc)->in0;
           break;
         case 1:
           return get_mult(fab,loc.idxloc)->in1;
           break;
        default:
           comm::error("unknown mult input");
           break;
      }
   case INTEG:
        return get_slice(fab,loc.idxloc.loc)->integrator->in0; 
        break;

   case TILE_INPUT:
        return get_slice(fab,loc.idxloc.loc)
                ->tileInps[loc.idx2].in0;
        break;

   case TILE_OUTPUT:
        return get_slice(fab,loc.idxloc.loc)
                ->tileOuts[loc.idx2].in0;
        break;

   case FANOUT:
        return get_fanout(fab,loc.idxloc)->in0;
        break;

   case CHIP_OUTPUT:
        return get_slice(fab,loc.idxloc.loc)->chipOutput->in0;
        break;

   case CHIP_INPUT:
        comm::error("no input port for chip_input");
        break;

   case LUT:
        comm::error("unhandled: lut");
        break;

  }
}


Fabric::Chip::Tile::Slice::FunctionUnit::Interface* get_output_port(Fabric * fab, uint16_t& btype, circ_loc_idx2_t& loc){
  switch(btype){
    case TILE_DAC:
      return get_slice(fab,loc.idxloc.loc)->dac->out0; 
      break;

    case MULT:
       return get_mult(fab,loc.idxloc)->out0;
       break;
       
   case INTEG:
        return get_slice(fab,loc.idxloc.loc)->integrator->in0; 
        break;
        
   case TILE_OUTPUT:
        return get_slice(fab,loc.idxloc.loc)
                ->tileOuts[loc.idx2].out0;
        break;

   case TILE_INPUT:
        return get_slice(fab,loc.idxloc.loc)
                ->tileInps[loc.idx2].out0;
        break;
        
   case FANOUT:
        switch(loc.idx2){
           case 0:
              return get_fanout(fab,loc.idxloc)->out0;
              break;
           case 1:
              return get_fanout(fab,loc.idxloc)->out1;
              break;
           case 2:
              return get_fanout(fab,loc.idxloc)->out2;
              break;    
         
           default:
              comm::error("unknown fanout output");
              break;
    
        }
        
   case CHIP_INPUT:
        return get_slice(fab,loc.idxloc.loc)->chipInput->out0;
        break;
        
   case CHIP_OUTPUT:
        comm::error("no output port for chip_output");
        break;

   case LUT:
        comm::error("unhandled: lut");
        break;
    
  }
}

void load_range(uint8_t range, bool * lo, bool * hi){
  switch(range){
    case 0:
      *lo = true;
      *hi = false;
      break;
    case 1:
      *lo = false;
      *hi = false;
      break;
    case 2:
      *lo = false;
      *hi = true;
      break;
    default:
      comm::error("[ERROR] unknown range");
      break;
  }
  
}

void load_dac_source(uint8_t source, bool * mem, bool * ext, bool * lut0, bool * lut1){
  *lut0 = false;
  *lut1 = false;
  *mem = false;
  *ext = false;
  switch(source){
    case circ::DS_MEM:
      *mem = true;
      break;
    case circ::DS_EXT:
      *ext = true;
      break;
    case circ::DS_LUT0:
      *lut0 = true;
      break;
    case circ::DS_LUT1:
      *lut1 = true;
      break;
    default:
      comm::error("[ERROR] unknown source");
  }
  
}

void load_lut_source(uint8_t source, bool * ext, bool * adc0, bool * adc1){
  *adc0 = false;
  *adc1 = false;
  *ext = false;
  switch(source){
    case circ::LS_EXT:
      *ext = true;
      break;
    case circ::LS_ADC0:
      *adc0 = true;
      break;
    case circ::LS_ADC1:
      *adc1 = true;
      break;
    default:
      comm::error("[ERROR] unknown source");
  }
  
}


Fabric* setup_board(){
  Fabric* fabric = new Fabric();
  return fabric;
}
void debug_command(Fabric * fab, cmd_t& cmd, float* inbuf){
  cmd_write_lut_t wrlutd;
  switch(cmd.type){
      case cmd_type_t::CONFIG_DAC:
        comm::response("[dbg] configured dac (direct)",0);
        break;
        
      case cmd_type_t::USE_ADC:
        comm::response("[dbg] enabled adc",0);
        break;
        
      case cmd_type_t::USE_DAC:
        comm::response("[dbg] enabled dac",0);
        break;
      
      case cmd_type_t::CONFIG_MULT:
        comm::response("[dbg] configured mult [direct]",0);
        break;
        
      case cmd_type_t::USE_MULT:
        comm::response("[dbg] enabled mult",0);
        break;
 
        
      case cmd_type_t::USE_FANOUT:
        comm::response("[dbg] enabled fanout",0);
        break;
   
    case cmd_type_t::CONFIG_INTEG:
        comm::response("[dbg] configured integ [direct]",0);
        break;
        
    case cmd_type_t::USE_INTEG:
        comm::response("[dbg] enabled integ",0);
        break;

    case cmd_type_t::GET_INTEG_STATUS:
        comm::response("[dbg] retrieved integ exception",1);
        comm::data("0", "i");
        break;
    case cmd_type_t::GET_ADC_STATUS:
        comm::response("[dbg] retrieved  lut exception",1);
        comm::data("0", "i");
        break;
        
    case cmd_type_t::USE_LUT:
        comm::response("[dbg] use lut",0);
        break;

    case cmd_type_t::WRITE_LUT:
       wrlutd = cmd.data.write_lut;
       comm::print_header();
       Serial.print(wrlutd.n);
       Serial.print(" offset=");
       Serial.println(wrlutd.offset);
       for(int data_idx=0; data_idx < wrlutd.n; data_idx+=1){
          comm::print_header();
          Serial.print(data_idx+wrlutd.offset);
          Serial.print("=");
          Serial.print(inbuf[data_idx]);
        }
        comm::response("[dbg] write lut",0);
        
        break;
        
    case cmd_type_t::DISABLE_DAC:
        comm::response("[dbg] disabled dac",0);
        break;
    
    case cmd_type_t::DISABLE_ADC:
        comm::response("[dbg] disabled adc",0);
        break;
    
    case cmd_type_t::DISABLE_LUT:
        comm::response("[dbg] disabled lut",0);
        break;
         
    case cmd_type_t::DISABLE_MULT:
        comm::response("[dbg] disabled mult",0);
        break;

    case cmd_type_t::DISABLE_FANOUT:
        comm::response("[dbg] disabled fanout",0);
        break;

    case cmd_type_t::DISABLE_INTEG:
        comm::response("[dbg] disabled integ",0);
        break;

    case cmd_type_t::CONNECT:
        comm::response("[dbg] connected",0);
        break;

    case cmd_type_t::BREAK:
        comm::response("[dbg] disconnected",0);
        break;
        
    case cmd_type_t::CALIBRATE:
        comm::response("[dbg] calibrated",0);
        break;
        
    default:
      comm::error("unknown command");
      break;
  }
  
}
void exec_command(Fabric * fab, cmd_t& cmd, float* inbuf){
  cmd_use_dac_t dacd;
  cmd_use_mult_t multd;
  cmd_use_fanout_t fod;
  cmd_use_integ_t integd;
  cmd_use_lut_t lutd;
  cmd_write_lut_t wrlutd;
  cmd_use_adc_t adcd;
  cmd_connection_t connd;
  bool lo1,hi1;
  bool lo2,hi2;
  bool lo3,hi3;
  bool s1,s2,s3,s4;
  uint8_t byteval;
  char buf[16];
  Fabric::Chip::Tile::Slice* slice;
  Fabric::Chip::Tile::Slice::Dac* dac;
  Fabric::Chip::Tile::Slice::Multiplier * mult;
  Fabric::Chip::Tile::Slice::Fanout * fanout;
  Fabric::Chip::Tile::Slice::Integrator* integ;
  Fabric::Chip::Tile::Slice::LookupTable* lut;
  Fabric::Chip::Tile::Slice::ChipAdc * adc;
  Fabric::Chip::Tile::Slice::FunctionUnit::Interface* src;
  Fabric::Chip::Tile::Slice::FunctionUnit::Interface* dst;
  
  switch(cmd.type){
      case cmd_type_t::CONFIG_DAC:
        dacd = cmd.data.dac; 
        dac = get_slice(fab,dacd.loc)->dac;
        load_range(dacd.out_range, &lo1, &hi1);
        if(dacd.source == circ::dac_source::DS_MEM){
          comm::test(dac->setConstantDirect(dacd.value,hi1,true), 
             "failed to configure dac value");
        }
        comm::response("configured dac (direct)",0);
        break;
        
      case cmd_type_t::USE_ADC:
        adcd = cmd.data.adc; 
        adc = get_slice(fab,adcd.loc)->adc;
        adc->setEnable(true);
        load_range(adcd.in_range, &lo1, &hi1);
        adc->setHiRange(hi1);
        comm::response("enabled adc",0);
        break;
        
      case cmd_type_t::USE_DAC:
        dacd = cmd.data.dac; 
        dac = get_slice(fab,dacd.loc)->dac;
        dac->setEnable(true);
        dac->out0->setInv(dacd.inv);
        load_range(dacd.out_range, &lo1, &hi1);
        dac->setHiRange(hi1);
        load_dac_source(dacd.source, &s1, &s2, &s3, &s4);
        dac->setSource(s1,s2,s3,s4);
        if(dacd.source == circ::dac_source::DS_MEM){
          comm::test(dac->setConstantDirect(dacd.value,hi1,false), 
            "failed to set dac value");
        }
        comm::response("enabled dac",0);
        break;
      
      case cmd_type_t::CONFIG_MULT:
        // multiplier doesn't actually support inversion
        // multiplier uses dac from same row.
        multd = cmd.data.mult;
        mult = get_mult(fab,multd.loc);
        if(multd.use_coeff){
          // determine if we're in the high or low output range.
          load_range(multd.out_range, &lo1, &hi1);
          comm::test(mult->setGainDirect(multd.coeff, hi1, true),
             "failed to set gain");
        }
        comm::response("configured mult [direct]",0);
        break;
        
      case cmd_type_t::USE_MULT:
        // multiplier doesn't actually support inversion
        // multiplier uses dac from same row.
        multd = cmd.data.mult;
        mult = get_mult(fab,multd.loc);
        mult->setEnable(true);
        mult->setVga(multd.use_coeff);
        load_range(multd.in0_range, &lo1, &hi1);
        load_range(multd.in1_range, &lo2, &hi2);
        load_range(multd.out_range, &lo3, &hi3);
        mult->in0->setRange(lo1,hi1);
        mult->out0->setRange(lo3,hi3);
        if(not multd.use_coeff){
           mult->in1->setRange(lo2,hi2);
        }
        else{
          comm::test(mult->setGainDirect(multd.coeff, hi3, false),
             "failed to set gain");
        }
        comm::response("enabled mult",0);
        break;
 
        
      case cmd_type_t::USE_FANOUT:
        fod = cmd.data.fanout;
        fanout = get_fanout(fab,fod.loc);
        fanout->setEnable(true);
        load_range(fod.in_range, &lo1, &hi1);
        assert(!lo1);
        fanout->setHiRange(hi1);
        fanout->out0->setInv(fod.inv[0]);
        fanout->out1->setInv(fod.inv[1]);
        fanout->out2->setInv(fod.inv[2]);
        comm::response("enabled fanout",0);
        break;
   
    case cmd_type_t::CONFIG_INTEG:
        integd = cmd.data.integ;
        integ = get_slice(fab,integd.loc)->integrator;
        load_range(integd.out_range, &lo1, &hi1);
        comm::test(integ->setInitialDirect(integd.value, hi1, true),
            "failed to set integ value");
        comm::response("configured integ [direct]",0);
        break;
        
    case cmd_type_t::USE_INTEG:
        integd = cmd.data.integ;
        integ = get_slice(fab,integd.loc)->integrator;
        integ->setEnable(true);
        integ->setException( integd.debug == 1 ? true : false);
        integ->out0->setInv(integd.inv);
        load_range(integd.in_range, &lo1, &hi1);
        load_range(integd.out_range, &lo2, &hi2);
        integ->in0->setRange(lo1,hi1);
        integ->out0->setRange(lo2,hi2);
        comm::test(integ->setInitialDirect(integd.value, hi2, false),
            "failed to set integ value");
        comm::response("enabled integ",0);
        break;

    case cmd_type_t::GET_INTEG_STATUS:
        integ = get_slice(fab,cmd.data.circ_loc)->integrator;
        comm::response("retrieved integ exception",1);
        comm::data(integ->getException() ? "1" : "0", "i");
        break;
    case cmd_type_t::GET_ADC_STATUS:
        adc = get_slice(fab,cmd.data.circ_loc)->adc;
        comm::response("retrieved  lut exception",1);
        sprintf(buf,"%d",adc->getStatusCode());
        comm::data(buf, "i");
        break;
        
    case cmd_type_t::USE_LUT:
        lutd = cmd.data.lut;
        lut = get_slice(fab,lutd.loc)->lut; 
        load_lut_source(lutd.source, &s1, &s2, &s3);
        lut->setSource(s1,s2,s3);
        comm::response("use lut",0);
        break;
        
    case cmd_type_t::WRITE_LUT:
        wrlutd = cmd.data.write_lut;
        lut = get_slice(fab,wrlutd.loc)->lut; 
        for(int data_idx=0; data_idx < wrlutd.n; data_idx+=1){
          byteval = round(inbuf[data_idx]*128.0 + 128.0);
          comm::print_header();
          Serial.print(data_idx+wrlutd.offset);
          Serial.print("=");
          Serial.print(inbuf[data_idx]);
          Serial.print("; ");
          Serial.println(byteval);
          if(inbuf[data_idx] < -1.0 || inbuf[data_idx] > 1.0){
            comm::error("lut value not in <-1,1>");
          }
          lut->setLut(wrlutd.offset+data_idx,byteval);
        }
        comm::response("write lut",0);
        break;

    case cmd_type_t::DISABLE_DAC:
        dac = get_slice(fab,cmd.data.circ_loc)->dac;
        dac->setEnable(false);
        comm::response("disabled dac",0);
        break;

    case cmd_type_t::DISABLE_ADC:
        adc = get_slice(fab,cmd.data.circ_loc)->adc;
        adc->setEnable(false);
        comm::response("disabled adc",0);
        break;

     case cmd_type_t::DISABLE_LUT:
        lut = get_slice(fab,cmd.data.circ_loc)->lut;
        //lut->setEnable(false);
        comm::response("disabled lut",0);
        break;

    case cmd_type_t::DISABLE_MULT:
        multd = cmd.data.mult;
        mult = get_mult(fab,multd.loc);
        mult->setEnable(false);
        comm::response("disabled mult",0);
        break;

    case cmd_type_t::DISABLE_FANOUT:
        fod = cmd.data.fanout;
        fanout = get_fanout(fab,fod.loc);
        fanout->setEnable(false);
        comm::response("disabled fanout",0);
        break;

    case cmd_type_t::DISABLE_INTEG:
        integd = cmd.data.integ;
        integ = get_slice(fab,integd.loc)->integrator;
        integ->setEnable(false);
        comm::response("disabled integ",0);
        break;

    case cmd_type_t::CONNECT:
        connd = cmd.data.conn;
        src = get_output_port(fab,connd.src_blk,connd.src_loc);
        dst = get_input_port(fab,connd.dst_blk,connd.dst_loc);
        Fabric::Chip::Connection(src,dst).setConn();
        comm::response("connected",0);
        break;

    case cmd_type_t::BREAK:
        connd = cmd.data.conn;
        src = get_output_port(fab,connd.src_blk,connd.src_loc);
        dst = get_input_port(fab,connd.dst_blk,connd.dst_loc);
        Fabric::Chip::Connection(src,dst).brkConn();
        comm::response("disconnected",0);
        break;

    case cmd_type_t::CALIBRATE:
        slice = get_slice(fab,cmd.data.circ_loc);
        if(do_calibrate(cmd.data.circ_loc.chip,
                        cmd.data.circ_loc.tile,
                        cmd.data.circ_loc.slice)){
          comm::test(slice->calibrate(), "calibration failed");
        }
        else{
          comm::print_header();
          Serial.println("skipping calibration.");
          Serial.flush();
        }
        comm::response("calibrated",0);
        break;

   default:
      comm::error("unknown command");
      break;
  }
  
}


void print_loc(circ_loc_t& loc){
  Serial.print(loc.chip);
  Serial.print(":");
  Serial.print(loc.tile);
  Serial.print(":");
  Serial.print(loc.slice);
}

void print_idx_loc(circ_loc_idx1_t& loc){
  print_loc(loc.loc);
  Serial.print(":");
  Serial.print(loc.idx);
}


void print_port_loc(circ_loc_idx2_t& loc){
  print_idx_loc(loc.idxloc);
  Serial.print("[");
  Serial.print(loc.idx2);
  Serial.print("]");
}

void print_block(uint8_t type){
  switch(type){
    case block_type::TILE_DAC:
      Serial.print("dac");
      break;
      
    case block_type::CHIP_INPUT:
      Serial.print("chip_in");
      break;
      
    case block_type::CHIP_OUTPUT:
      Serial.print("chip_out");
      break;

    case block_type::TILE_INPUT:
      Serial.print("tile_in");
      break;
    
    case block_type::TILE_OUTPUT:
      Serial.print("tile_out");
      break;
      
    case block_type::MULT:
      Serial.print("mult");
      break;

    case block_type::INTEG:
      Serial.print("integ");
      break;

    case block_type::FANOUT:
      Serial.print("fanout");
      break;

    case block_type::LUT:
      Serial.print("lut");
      break;

    case block_type::TILE_ADC:
      Serial.print("adc");
      break;
    default:
      Serial.print("unknown<");
      Serial.print(type);
      Serial.print(">");
      break;
  }
  
}
#define range_to_str(code) (code == 2 ? "h" : (code == 1 ? "m" : (code == 0 ? "l" : "?")))

void print_command(cmd_t& cmd){
  comm::print_header();
  switch(cmd.type){
      case cmd_type_t::USE_FANOUT:
        Serial.print("use fanout ");
        print_idx_loc(cmd.data.fanout.loc);
        Serial.print(" inv0=");
        Serial.print(cmd.data.fanout.inv[0] ? "yes" : "no");
        Serial.print(" inv1=");
        Serial.print(cmd.data.fanout.inv[1] ? "yes" : "no");
        Serial.print(" inv2=");
        Serial.print(cmd.data.fanout.inv[2] ? "yes" : "no");
        Serial.print(" rng=");
        Serial.print(range_to_str(cmd.data.fanout.in_range));
        break;
        
      case cmd_type_t::CONFIG_MULT:
        Serial.print("config mult ");
        print_idx_loc(cmd.data.mult.loc);
        if(cmd.data.mult.use_coeff){
          Serial.print(" gain coeff=");
          Serial.print(cmd.data.mult.coeff);
        }
        else{
          Serial.print(" prod");
        }
        Serial.print(" in0_rng=");
        Serial.print(range_to_str(cmd.data.mult.in0_range));
        Serial.print(" in1_rng=");
        Serial.print(range_to_str(cmd.data.mult.in1_range));
        Serial.print(" out_rng=");
        Serial.print(range_to_str(cmd.data.mult.out_range));
        break;
        
      case cmd_type_t::USE_MULT:
        Serial.print("use mult ");
        print_idx_loc(cmd.data.mult.loc);
        if(cmd.data.mult.use_coeff){
          Serial.print(" gain coeff=");
          Serial.print(cmd.data.mult.coeff);
        }
        else{
          Serial.print(" prod");
        }
        Serial.print(" in0_rng=");
        Serial.print(range_to_str(cmd.data.mult.in0_range));
        Serial.print(" in1_rng=");
        Serial.print(range_to_str(cmd.data.mult.in1_range));
        Serial.print(" out_rng=");
        Serial.print(range_to_str(cmd.data.mult.out_range));
        break;

      case cmd_type_t::CONFIG_DAC:
        Serial.print("config dac ");
        print_loc(cmd.data.dac.loc);
        Serial.print(" val=");
        Serial.print(cmd.data.dac.value);
        break;

      case cmd_type_t::USE_ADC:
        Serial.print("use adc ");
        print_loc(cmd.data.adc.loc);
        Serial.print(" rng=");
        Serial.print(range_to_str(cmd.data.adc.in_range));
        break;
        
      case cmd_type_t::USE_DAC:
        Serial.print("use dac ");
        print_loc(cmd.data.dac.loc);
        Serial.print(" src=");
        Serial.print(cmd.data.dac.source);
        Serial.print(" inv=");
        Serial.print(cmd.data.dac.inv ? "yes" : "no");
        Serial.print(" rng=");
        Serial.print(range_to_str(cmd.data.dac.out_range));
        Serial.print(" val=");
        Serial.print(cmd.data.dac.value);
        break;
        
      case cmd_type_t::GET_ADC_STATUS:
        Serial.print("get adc status ");
        print_loc(cmd.data.adc.loc);
        break;
        
      case cmd_type_t::GET_INTEG_STATUS:
        Serial.print("get integ status ");
        print_loc(cmd.data.integ.loc);
        break;
        
      case cmd_type_t::CONFIG_INTEG:
        Serial.print("config integ ");
        print_loc(cmd.data.integ.loc);
        Serial.print(" ic=");
        Serial.print(cmd.data.integ.value);
        Serial.print(" in_range=");
        Serial.print(range_to_str(cmd.data.integ.in_range));
        Serial.print(" out_range=");
        Serial.print(range_to_str(cmd.data.integ.out_range));
        break;
        
      case cmd_type_t::USE_INTEG:
        Serial.print("use integ ");
        print_loc(cmd.data.integ.loc);
        Serial.print(" inv=");
        Serial.print(cmd.data.integ.inv ? "yes" : "no");
        Serial.print(" in_range=");
        Serial.print(range_to_str(cmd.data.integ.in_range));
        Serial.print(" out_range=");
        Serial.print(range_to_str(cmd.data.integ.out_range));
        Serial.print(" debug=");
        Serial.print(cmd.data.integ.debug == 1 ? "yes" : "no");
        break;
        
      case cmd_type_t::USE_LUT:
        Serial.print("use lut ");
        print_loc(cmd.data.lut.loc);
        Serial.print(" src=");
        Serial.print(cmd.data.lut.source);
        break;
      
      case cmd_type_t::WRITE_LUT:
        Serial.print("write lut ");
        print_loc(cmd.data.circ_loc);
        break;
        
      case cmd_type_t::DISABLE_ADC:
        Serial.print("disable adc ");
        print_loc(cmd.data.circ_loc);
        break;
        
      case cmd_type_t::DISABLE_DAC:
        Serial.print("disable dac ");
        print_loc(cmd.data.circ_loc);
        break;
        
      case cmd_type_t::DISABLE_MULT:
        Serial.print("disable mult ");
        print_loc(cmd.data.circ_loc);
        break;
        
      case cmd_type_t::DISABLE_INTEG:
        Serial.print("disable integ ");
        print_loc(cmd.data.circ_loc);
        break;
        
      case cmd_type_t::DISABLE_FANOUT:
        Serial.print("disable fanout ");
        print_idx_loc(cmd.data.circ_loc_idx1);
        break;
        
      case cmd_type_t::DISABLE_LUT:
        Serial.print("disable lut ");
        print_loc(cmd.data.circ_loc);
        break;
        
      case cmd_type_t::CONNECT:
        Serial.print("conn ");
        print_block(cmd.data.conn.src_blk);
        Serial.print(" ");
        print_port_loc(cmd.data.conn.src_loc);
        Serial.print("<->");
        print_block(cmd.data.conn.dst_blk);
        Serial.print(" ");
        print_port_loc(cmd.data.conn.dst_loc);
        break;
        
      case cmd_type_t::BREAK:
        Serial.print("break ");
        print_block(cmd.data.conn.src_blk);
        Serial.print(" ");
        print_port_loc(cmd.data.conn.src_loc);
        Serial.print("<->");
        print_block(cmd.data.conn.dst_blk);
        Serial.print(" ");
        print_port_loc(cmd.data.conn.dst_loc);
        break;
        
      case cmd_type_t::CALIBRATE:
        Serial.print("calibrate ");
        print_loc(cmd.data.circ_loc);
        break;

      default:
        Serial.print(cmd.type);
        Serial.print(" <unimpl circuit>");
        break;
  }
  Serial.println("");
}


}


