import lab_bench.lib.chip_command as chip_cmd
import lab_bench.lib.exp_command as exp_cmd
import lab_bench.lib.command as toplevel_cmd
from lang.hwenv import DiffPinMode

class GrendelProg:

  def __init__(self):
    self._stmts = []

  def validate(self,cmd):
    cmdstr = str(cmd)
    args = cmdstr.split()
    assert(cmd.__class__.name() == args[0])
    test = cmd.__class__.parse(args)
    if(test is None):
      raise Exception("failed to validate: %s" % cmd)


  def add(self,cmd):
    self.validate(cmd)
    self._stmts.append(cmd)

  def __repr__(self):
    st = ""
    for stmt in self._stmts:
      st += "%s\n" % stmt

    return st

  def write(self,filename):
    with open(filename,'w') as fh:
      for stmt in self._stmts:
        fh.write("%s\n" % stmt)

def cast_enum(tup,type_tup):
  vs = []
  for vstr,T in zip(tup,type_tup):
    vs.append(T(vstr))

  return vs

def gen_unpack_loc(circ,locstr):
  loc =circ.board.key_to_loc(locstr)
  index = None
  if len(loc) == 5:
    chip,tile,slce,index = loc[1:]
  elif len(loc) == 4:
    chip,tile,slce = loc[1:]
  else:
    raise Exception("unexpected loc: %s" % str(loc))

  return chip,tile,slce,index

def gen_use_dac(circ,block,locstr,config):
  chip,tile,slce,_ =gen_unpack_loc(circ,locstr)
  inv,rng = cast_enum(config.scale_mode,\
                      [chip_cmd.SignType,chip_cmd.RangeType])

  value = config.dac('in')
  return chip_cmd.UseDACCmd(chip, \
                            tile, \
                            slce, \
                            value=value, \
                            inv=inv, \
                            out_range=rng)


def gen_get_integrator_status(circ,block,locstr):
  chip,tile,slce,_ =gen_unpack_loc(circ,locstr)
  return chip_cmd.GetIntegStatusCmd(chip,
                                 tile,
                                 slce)


def gen_use_integrator(circ,block,locstr,config,debug=True):
  chip,tile,slce,_ =gen_unpack_loc(circ,locstr)
  inv,in_rng,out_rng = cast_enum(config.scale_mode,
                                   [chip_cmd.SignType, \
                                    chip_cmd.RangeType, \
                                    chip_cmd.RangeType])
  init_cond = config.dac('ic')
  return chip_cmd.UseIntegCmd(chip,
                              tile,
                              slce,
                              init_cond=init_cond,
                              inv=inv,
                              in_range=in_rng,
                              out_range=out_rng,
                              debug=debug)


def gen_use_multiplier(circ,block,locstr,config):
  MODE_MAP = {"mul":False,'vga':True}

  chip,tile,slce,index =gen_unpack_loc(circ,locstr)
  use_coeff = MODE_MAP[config.comp_mode]
  if use_coeff:
    in0_rng,out_rng = cast_enum(config.scale_mode, \
                                [chip_cmd.RangeType,chip_cmd.RangeType])
    coeff = config.dac('coeff')
    return chip_cmd.UseMultCmd(chip,
                               tile,
                               slce,
                               index,
                               in0_range=in0_rng,
                               out_range=out_rng,
                               coeff=coeff,
                               use_coeff=True)

  else:
    in0_rng,in1_rng,out_rng = cast_enum(config.scale_mode, \
                                [chip_cmd.RangeType, \
                                 chip_cmd.RangeType, \
                                 chip_cmd.RangeType])

    return chip_cmd.UseMultCmd(chip,
                               tile,
                               slce,
                               index,
                               in0_range=in0_rng,
                               in1_range=in1_rng,
                               out_range=out_rng)

def gen_use_fanout(circ,block,locstr,config):
  INV_MAP = {'pos':False,'neg':True}

  chip,tile,slce,index =gen_unpack_loc(circ,locstr)
  inv0,inv1,inv2,in_rng = cast_enum(config.scale_mode,
                                    [chip_cmd.SignType,
                                     chip_cmd.SignType,
                                     chip_cmd.SignType,
                                     chip_cmd.RangeType])
  return chip_cmd.UseFanoutCmd(chip,tile,slce,index,
                               in_range=in_rng,
                               inv0=inv0,
                               inv1=inv1,
                               inv2=inv2)


def gen_block(gprog,circ,block,locstr,config):
  if block.name == 'multiplier':
    cmd = gen_use_multiplier(circ,block,locstr,config)
    gprog.add(cmd)

  elif block.name == 'tile_dac':
    cmd = gen_use_dac(circ,block,locstr,config)
    gprog.add(cmd)

  elif block.name == 'integrator':
    cmd = gen_use_integrator(circ,block,locstr,config,debug=True)
    gprog.add(cmd)
    cmd = gen_get_integrator_status(circ,block,locstr)
    gprog.add(cmd)

  elif block.name == 'fanout':
    cmd = gen_use_fanout(circ,block,locstr,config)
    gprog.add(cmd)

  elif block.name == 'ext_chip_in' or \
       block.name == 'tile_in' or \
       block.name == 'chip_in' or \
       block.name == 'ext_chip_out' or \
       block.name == 'tile_out' or \
       block.name == 'chip_out':
    return

  else:
    raise Exception("unimplemented: <%s>" % block.name)

def gen_conn(gprog,circ,sblk,slocstr,sport,dblk,dlocstr,dport):
  TO_BLOCK_TYPE = {
    'dac': 'dac',
    'integrator': 'integ',
    'fanout': 'fanout',
    'tile_out': 'tile_output',
    'tile_in': 'tile_input',
    'tile_dac': 'dac',
    'multiplier':'mult',
    'ext_chip_in': 'chip_input',
    'ext_chip_out': 'chip_output'
  }
  TO_PORT_ID = {
    'in' : 0,
    'in0' : 0,
    'in1' : 1,
    'out' : 0,
    'out0' : 0,
    'out1' : 1,
    'out2' : 2
  }
  chip,tile,slce,index =gen_unpack_loc(circ,slocstr)
  src_port = TO_PORT_ID[sport]
  src_loc = chip_cmd.CircPortLoc(chip,tile,slce,src_port,index=index)
  src_blk = TO_BLOCK_TYPE[sblk]

  chip,tile,slce,index =gen_unpack_loc(circ,dlocstr)
  dest_port = TO_PORT_ID[dport]
  dest_loc = chip_cmd.CircPortLoc(chip,tile,slce,dest_port,index=index)
  dest_blk = TO_BLOCK_TYPE[dblk]

  cmd = chip_cmd.MakeConnCmd(src_blk, \
                               src_loc, \
                               dest_blk,
                               dest_loc)
  gprog.add(cmd)


def parse(line):
  cmd = toplevel_cmd.parse(line)
  assert(not cmd is None)
  cmd = toplevel_cmd.parse(str(cmd))
  assert(not cmd is None)
  return cmd

def get_ext_dacs_in_use(board,conc_circ,menv):
  info = {}
  for loc,config in conc_circ.instances_of_block('ext_chip_in'):
    waveform,periodic = menv.input(config.label('in'))
    handle = board.handle_by_inst('ext_chip_in',loc)
    assert(not handle is None)
    info[handle] = {'label':config.label('in'),
                    'scf':config.scf('in'),
                    'waveform':waveform,
                    'periodic':periodic}


  return info

def get_ext_adcs_in_use(board,conc_circ,menv):
  info = {}
  for loc,config in conc_circ.instances_of_block('ext_chip_out'):
    handle = board.handle_by_inst('ext_chip_out',loc)
    info[handle] = {'label':config.label('out'),
                    'scf':config.scf('out')}


  return info


def preamble(gren,board,conc_circ,mathenv,hwenv):
  dacs_in_use = get_ext_dacs_in_use(board,conc_circ,mathenv)
  adcs_in_use = get_ext_adcs_in_use(board,conc_circ,mathenv)
  # compute times
  tau = conc_circ.tau
  tc = board.time_constant
  scaled_tc_s = tc/tau
  scaled_tc_us = tc/tau*1e6
  scaled_sim_time = mathenv.sim_time*scaled_tc_s
  scaled_input_time = mathenv.input_time*scaled_tc_s
  gren.add(parse('micro_reset'))
  # initialize oscilloscope
  if hwenv.use_oscilloscope:
    gren.add(parse('micro_use_osc'))
    for chan,lb,ub in hwenv.oscilloscope.chan_ranges():
       cmd = "osc_set_volt_range %d %f %f" % (chan,lb,ub)
       gren.add(parse(cmd))
       cmd = "osc_set_sim_time %f" % \
             (scaled_sim_time)
       gren.add(parse(cmd))

  # initialize microcontroller
  cmd = "micro_set_sim_time %f %f" % \
             (scaled_sim_time,scaled_input_time)
  gren.add(parse(cmd))

  # flag adc/dac data for storage in buffer
  for handle in adcs_in_use.keys():
    out_no = hwenv.adc(handle)
    if not out_no is None:
      gren.add(parse('micro_use_adc %d' % out_no))

  for handle,info in dacs_in_use.items():
    in_no = hwenv.dac(handle)
    gren.add(parse('micro_use_dac %d %s' % \
                   (in_no,info['periodic'])))


  gren.add(parse('micro_compute_offsets'))
  gren.add(parse('micro_get_num_adc_samples'))
  gren.add(parse('micro_get_num_dac_samples'))
  gren.add(parse('micro_get_time_delta'))
  #FIXME `use_due_dac` if there are external inputs
  #FIXME `use_due_adc` / `use_osc` if there are external outputs
  gren.add(parse('micro_use_chip'))

  for handle,info in dacs_in_use.items():
    in_no = hwenv.dac(handle)
    gren.add(parse('micro_set_dac_values %d %s %f %f' % \
                   (in_no,info['waveform'],\
                    1.0/scaled_tc_s,
                    info['scf']
                   )
    ))

def postconfig(path_handler,gren,board,conc_circ,menv,hwenv,filename):
  if hwenv.use_oscilloscope:
    gren.add(parse('osc_setup_trigger'))
  gren.add(parse('micro_setup_chip'))
  gren.add(parse('micro_get_overflows'))
  gren.add(parse('micro_run'))
  gren.add(parse('micro_get_overflows'))
  gren.add(parse('micro_teardown_chip'))


  circ_bmark,circ_indices,circ_scale_index,_,_ = \
                    path_handler.grendel_file_to_args(filename)



  adcs_in_use = get_ext_adcs_in_use(board,conc_circ,menv)

  for handle, info in adcs_in_use.items():
    out_no = hwenv.adc(handle)
    filename = path_handler.measured_waveform_file(circ_bmark, \
                                                   circ_indices, \
                                                   circ_scale_index, \
                                                   menv.name, \
                                                   hwenv.name, \
                                                   info['label'])
    if not out_no is None:
      gren.add(parse('micro_get_adc_values %d %s %s' % (out_no, \
                                                        info['label'], \
                                                        filename)))
    elif hwenv.use_oscilloscope:
      pin_mode = hwenv.oscilloscope.output(handle)
      if isinstance(pin_mode,DiffPinMode):
          gren.add(parse('osc_get_values differential %d %d %s %s' % \
                         (pin_mode.low,pin_mode.high, \
                          info['label'], \
                          filename)))
      else:
        raise Exception("unknown pinmode")
    else:
      raise Exception("cannot read value")


  return gren

def generate(paths,board,conc_circ,menv,hwenv,filename):
  gren = GrendelProg()
  preamble(gren,board,conc_circ,menv,hwenv)
  for block_name,loc,config in conc_circ.instances():
    block = conc_circ.board.block(block_name)
    gen_block(gren,conc_circ,block,loc,config)

  for sblk,sloc,sport, \
      dblk,dloc,dport in conc_circ.conns():
    gen_conn(gren,conc_circ,sblk,sloc,sport, \
             dblk,dloc,dport)

  postconfig(paths,gren,board,conc_circ,menv,hwenv,filename)
  return gren
