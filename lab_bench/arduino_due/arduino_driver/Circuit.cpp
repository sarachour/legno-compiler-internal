#define _DUE
#include <HCDC_DEMO_API.h>
#include "Circuit.h"
#include <assert.h>

char HCDC_DEMO_BOARD = 4;

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

Fabric::Chip::Tile::Slice::FunctionUnit::Interface* get_input_port(Fabric * fab, uint16_t& btype, circ_loc_idx2_t& loc){
  switch(btype){
    case DAC:
      Serial.println("dac has no input port");
      exit(1);
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
           Serial.println("unknown mult input");
           exit(1);
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
        Serial.println("no input port for chip_input");
        exit(1);
        break;

   case LUT:
        Serial.println("unhandled: lut");
        exit(1);
        break;
    
  }
}


Fabric::Chip::Tile::Slice::FunctionUnit::Interface* get_output_port(Fabric * fab, uint16_t& btype, circ_loc_idx2_t& loc){
  switch(btype){
    case DAC:
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
              Serial.println("unknown fanout output");
              exit(1);
              break;
    
        }
        
   case CHIP_INPUT:
        return get_slice(fab,loc.idxloc.loc)->chipInput->out0;
        break;
        
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
float load_scf(uint8_t range){
    switch(range){
      case 0:
        return 0.1;
      case 1:
        return 1.0;
      case 2:
        return 10.0; 
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
      Serial.println("[ERROR] unknown range");
      exit(1);
      
  }
  
}

void commit_config(Fabric * fab){
   fab->cfgCommit();
}

void finalize_config(Fabric * fab){
  fab->cfgStop();
}

void execute(Fabric * fab){
  fab->execStart();
}

void finish(Fabric * fab){
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
  bool lo1,hi1;
  bool lo2,hi2;
  bool lo3,hi3;
  float scf;
  Fabric::Chip::Tile::Slice* slice;
  Fabric::Chip::Tile::Slice::Dac* dac;
  Fabric::Chip::Tile::Slice::Multiplier * mult;
  Fabric::Chip::Tile::Slice::Fanout * fanout;
  Fabric::Chip::Tile::Slice::Integrator* integ;
  Fabric::Chip::Tile::Slice::FunctionUnit::Interface* src;
  Fabric::Chip::Tile::Slice::FunctionUnit::Interface* dst;
  
  switch(cmd.type){
      case cmd_type_t::CONFIG_DAC:
        dacd = cmd.data.dac; 
        dac = get_slice(fab,dacd.loc)->dac;
        dac->setConstant(dacd.value);
        Serial.println("configured dac");
        break;
        
      case cmd_type_t::USE_DAC:
        dacd = cmd.data.dac; 
        dac = get_slice(fab,dacd.loc)->dac;
        dac->setEnable(true);
        dac->out0->setInv(dacd.inv);
        //dac->setConstant(dacd.value);
        Serial.println("enabled dac");
        break;
      
      case cmd_type_t::CONFIG_MULT:
        // multiplier doesn't actually support inversion
        // multiplier uses dac from same row.
        multd = cmd.data.mult;
        mult = get_mult(fab,multd.loc);
        load_range(multd.in0_range, &lo1, &hi1);
        load_range(multd.out_range, &lo2, &hi2);
        load_range(multd.in1_range, &lo3, &hi3);
        if(multd.use_coeff){
          scf = load_scf(multd.out_range)/load_scf(multd.in0_range);
          mult->setGain(multd.coeff*scf);
        }
        Serial.println("configured mult");
        break;
        
      case cmd_type_t::USE_MULT:
        // multiplier doesn't actually support inversion
        // multiplier uses dac from same row.
        multd = cmd.data.mult;
        mult = get_mult(fab,multd.loc);
        mult->setEnable(true);
        mult->setVga(multd.use_coeff);
        load_range(multd.in0_range, &lo1, &hi1);
        load_range(multd.out_range, &lo2, &hi2);
        load_range(multd.in1_range, &lo3, &hi3);
        if(not multd.use_coeff){
           mult->in0->setRange(lo1,hi1);
           mult->in0->setRange(lo2,hi2);
           mult->out0->setRange(lo3,hi3);
        }
        Serial.println("enabled mult");
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
        Serial.println("enabled fanout");
        break;
   
    case cmd_type_t::CONFIG_INTEG:
        integd = cmd.data.integ;
        integ = get_slice(fab,integd.loc)->integrator;
        integ->setException( integd.debug == 1 ? true : false);
        scf = load_scf(integd.out_range)/load_scf(integd.in_range);
        integ->setInitial(integd.value*scf);
        Serial.println("configured integ");
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
        Serial.println("enabled integ");
        break;

    case cmd_type_t::GET_INTEG_STATUS:
        integ = get_slice(fab,cmd.data.circ_loc)->integrator;
        Serial.println("retrieved exception");
        Serial.println(integ->getException() ? 1 : 0);
        break;
        
    case cmd_type_t::DISABLE_DAC:
        dac = get_slice(fab,cmd.data.circ_loc)->dac;
        dac->setEnable(false);
        Serial.println("disabled dac");
        break;

    case cmd_type_t::DISABLE_MULT:
        multd = cmd.data.mult;
        mult = get_mult(fab,multd.loc);
        mult->setEnable(false);
        Serial.println("disabled mult");
        break;

    case cmd_type_t::DISABLE_FANOUT:
        fod = cmd.data.fanout;
        fanout = get_fanout(fab,fod.loc);
        fanout->setEnable(false);
        Serial.println("disabled fanout");
        break;

    case cmd_type_t::DISABLE_INTEG:
        integd = cmd.data.integ;
        integ = get_slice(fab,integd.loc)->integrator;
        integ->setEnable(false);
        Serial.println("disabled integ");
        break;

    case cmd_type_t::CONNECT:
        connd = cmd.data.conn;
        src = get_output_port(fab,connd.src_blk,connd.src_loc);
        dst = get_input_port(fab,connd.dst_blk,connd.dst_loc);
        Fabric::Chip::Connection(src,dst).setConn();
        Serial.println("connected");
        break;

    case cmd_type_t::BREAK:
        connd = cmd.data.conn;
        src = get_output_port(fab,connd.src_blk,connd.src_loc);
        dst = get_input_port(fab,connd.dst_blk,connd.dst_loc);
        Fabric::Chip::Connection(src,dst).brkConn();
        Serial.println("disconnected");
        break;
        
    case cmd_type_t::CALIBRATE:
        slice = get_slice(fab,cmd.data.circ_loc);
        assert(slice->calibrate());
        Serial.println("calibrated");
        break;
        
    default:
      Serial.println("[ERROR] unknown command");
      exit(1);
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
    case block_type::DAC:
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

    default:
      Serial.print("unknown<");
      Serial.print(type);
      Serial.print(">");
      break;
  }
  
}
#define range_to_str(code) (code == 2 ? "h" : (code == 1 ? "m" : (code == 0 ? "l" : "?")))

void print_command(cmd_t& cmd){
  switch(cmd.type){
      case cmd_type_t::USE_FANOUT:
        Serial.print("use fanout ");
        print_idx_loc(cmd.data.fanout.loc);
        Serial.print(" inv[0]=");
        Serial.print(cmd.data.fanout.inv[0] ? "yes" : "no");
        Serial.print(" inv[1]=");
        Serial.print(cmd.data.fanout.inv[1] ? "yes" : "no");
        Serial.print(" inv[2]=");
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
        
      case cmd_type_t::USE_DAC:
        Serial.print("use dac ");
        print_loc(cmd.data.dac.loc);
        Serial.print(" inv=");
        Serial.print(cmd.data.dac.inv ? "yes" : "no");
        Serial.print(" rng=");
        Serial.print(range_to_str(cmd.data.dac.out_range));
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


