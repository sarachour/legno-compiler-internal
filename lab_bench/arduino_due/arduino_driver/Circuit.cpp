#define _DUE
#include <HCDC_DEMO_API.h>
#include "Circuit.h"
#include <assert.h>

namespace circ {
  
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
       Serial.println("unknown...");
       exit(1);
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
       Serial.println("unknown...");
       exit(1);
       break;
  }
  return fanout;
}

Fabric::Chip::Tile::Slice::FunctionUnit::Interface* get_input_port(Fabric * fab, block_type_t& btype, circ_loc_idx2_t loc){
  switch(btype){
    case DAC:
      Serial.println("dac has no input port");
      exit(1);
      break;

    case MULT:
       switch(loc.idx2){
         case 0:
           return get_mult(fab,loc.idxloc)->in0;
         case 1:
           return get_mult(fab,loc.idxloc)->in1;
        default:
           Serial.println("unknown mult input");
           exit(1);
           break;
    
      }
   case INTEG:
        return get_slice(fab,loc.idxloc.loc)->integrator->in0; 
        break;
        
   case TILE:
        return get_slice(fab,loc.idxloc.loc)
                ->tileOuts[loc.idx2].in0;
        break;
        
   case FANOUT:
        return get_fanout(fab,loc.idxloc)->in0;
        
   case CHIP_OUTPUT:
        return get_slice(fab,loc.idxloc.loc)->chipOutput->in0;

   case CHIP_INPUT:
        Serial.println("no input port for chip_input");
        exit(1);
        break;

   case LUT:
        Serial.println("unhandled: lut");
        exit(1);
        break;
    
  }
}


Fabric::Chip::Tile::Slice::FunctionUnit::Interface* get_output_port(Fabric * fab, block_type_t& btype, circ_loc_idx2_t loc){
  switch(btype){
    case DAC:
      Serial.println("dac has no input port");
      exit(1);
      break;

    case MULT:
       return get_mult(fab,loc.idxloc)->out0;
       break;
       
   case INTEG:
        return get_slice(fab,loc.idxloc.loc)->integrator->in0; 
        break;
        
   case TILE:
        return get_slice(fab,loc.idxloc.loc)
                ->tileOuts[loc.idx2].in0;
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
              Serial.println("unknown fanout output");
              exit(1);
              break;
    
        }
        
   case CHIP_INPUT:
        return get_slice(fab,loc.idxloc.loc)->chipInput->out0;

   case CHIP_OUTPUT:
        Serial.println("no output port for chip_output");
        exit(1);
        break;

   case LUT:
        Serial.println("unhandled: lut");
        exit(1);
        break;
    
  }
}

void commit_config(Fabric * fab){
   fab->cfgCommit();
}

inline void finalize_config(Fabric * fab){
  fab->cfgStop();
}

inline void execute(Fabric * fab){
  fab->execStart();
}

inline void finish(Fabric * fab){
  fab->execStop();
}

Fabric* setup_board(){
  Fabric* fabric = new Fabric();
  return fabric;
}

void exec_command(Fabric * fab, cmd_t& cmd){
  cmd_use_dac_t dacd;
  cmd_use_mult_t multd;
  cmd_use_fanout_t fod;
  cmd_use_integ_t integd;
  cmd_connection_t connd;
  Fabric::Chip::Tile::Slice::Dac* dac;
  Fabric::Chip::Tile::Slice::Multiplier * mult;
  Fabric::Chip::Tile::Slice::Fanout * fanout;
  Fabric::Chip::Tile::Slice::Integrator* integ;
  Fabric::Chip::Tile::Slice::FunctionUnit::Interface* src;
  Fabric::Chip::Tile::Slice::FunctionUnit::Interface* dst;
  
  switch(cmd.type){
        
      case cmd_type_t::USE_DAC:
        dacd = cmd.data.dac; 
        dac = get_slice(fab,dacd.loc)->dac;
        dac->setEnable(true);
        dac->out0->setInv(dacd.inv);
        dac->setConstantCode(dacd.value);
        break;

      case cmd_type_t::USE_MULT:
        multd = cmd.data.mult;
        mult = get_mult(fab,multd.loc);
        mult->setEnable(true);
        mult->out0->setInv(multd.inv);
        mult->setVga(multd.use_coeff); 
        mult->setGainCode(multd.coeff);
        break;

      case cmd_type_t::USE_FANOUT:
        fod = cmd.data.fanout;
        fanout = get_fanout(fab,fod.loc);
        fanout->setEnable(true);
        fanout->out0->setInv(fod.inv[0]);
        fanout->out1->setInv(fod.inv[1]);
        fanout->out2->setInv(fod.inv[2]);
        break;

    case cmd_type_t::USE_INTEG:
        integd = cmd.data.integ;
        integ = get_slice(fab,integd.loc)->integrator;
        integ->setEnable(true);
        integ->out0->setInv(integd.inv);
        integ->setInitial(integd.value);
        break;
        
    case cmd_type_t::DISABLE_DAC:
        dac = get_slice(fab,cmd.data.circ_loc)->dac;
        dac->setEnable(false);
        break;

    case cmd_type_t::DISABLE_MULT:
        multd = cmd.data.mult;
        mult = get_mult(fab,multd.loc);
        mult->setEnable(false);
        break;

    case cmd_type_t::DISABLE_FANOUT:
        fod = cmd.data.fanout;
        fanout = get_fanout(fab,fod.loc);
        fanout->setEnable(false);
        break;

    case cmd_type_t::DISABLE_INTEG:
        integd = cmd.data.integ;
        integ = get_slice(fab,integd.loc)->integrator;
        integ->setEnable(false);    
        break;

    case cmd_type_t::CONNECT:
        connd = cmd.data.conn;
        src = get_output_port(fab,connd.src_blk,connd.src_loc);
        dst = get_input_port(fab,connd.dst_blk,connd.dst_loc);
        Fabric::Chip::Connection(src,dst).setConn();
        break;

    case cmd_type_t::BREAK:
        connd = cmd.data.conn;
        src = get_output_port(fab,connd.src_blk,connd.src_loc);
        dst = get_input_port(fab,connd.dst_blk,connd.dst_loc);
        Fabric::Chip::Connection(src,dst).brkConn();
        break;
        
    case cmd_type_t::CALIBRATE:
        assert(get_slice(fab,cmd.data.circ_loc)->calibrate());
        break;
        
    default:
      Serial.println("[ERROR] unknown command");
      exit(1);
      break;
  }
  
}


void print_command(cmd_t& cmd){
  switch(cmd.type){
    default:
      Serial.print(cmd.type);
      Serial.println(" <unimpl circuit>");
  }
}


}


