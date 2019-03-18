from lab_bench.lib.chipcmd.misc import *
from lab_bench.lib.chipcmd.use import *
from lab_bench.lib.chipcmd.conn import *
from lab_bench.lib.chipcmd.config import *
from lab_bench.lib.chipcmd.data import SignType,RangeType, CircPortLoc, \
  LUTSourceType,DACSourceType
import lab_bench.lib.command as toplevel_cmd
from lang.hwenv import DiffPinMode
import ops.op as op

class GrendelProg:

  def __init__(self):
    self._stmts = []

  def validate(self,cmd):
    cmdstr = str(cmd)
    args = cmdstr.split()
    if not (cmd.__class__.name() == args[0]):
      raise Exception("class %s doesn't return correct name (expected %s)" % \
                      (cmd.__class__.name(), args[0]))
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

def gen_use_lut(circ,block,locstr,config,source):
  chip,tile,slce,_ =gen_unpack_loc(circ,locstr)
  in_scf,in_ival = config.scf('in'),config.interval('in')
  out_scf,out_ival = config.scf('out'),config.interval('out')
  variables,expr = op.to_python(config.expr('out',inject=True))
  yield UseLUTCmd(chip,tile,slce,source=source)
  yield WriteLUTCmd(chip,tile,slce,variables,expr)

def nearest_value(value):
  if value == 0.0:
    return 0.0
  vals = np.linspace(-1,1,256)
  idx = (np.abs(vals - value)).argmin()
  return vals[idx]

def gen_use_adc(circ,block,locstr,config):
  chip,tile,slce,_ =gen_unpack_loc(circ,locstr)
  rng = cast_enum([config.scale_mode],\
                  [RangeType])

  yield UseADCCmd(chip,tile,slce,
                           in_range=rng[0])

def gen_use_dac(circ,block,locstr,config,source,no_calib=False):
  chip,tile,slce,_ =gen_unpack_loc(circ,locstr)
  inv,rng = cast_enum(config.scale_mode,\
                      [SignType,RangeType])

  scf = config.scf('in') if config.has_scf('in') else 1.0
  if not config.dac('in') is None:
    value = config.dac('in')*scf
  else:
    assert(not source == DACSourceType.MEM)
    value = 0.0

  value = nearest_value(value)
  yield UseDACCmd(chip, \
                  tile, \
                  slce, \
                  value=value, \
                  inv=inv, \
                  out_range=rng,
                  source=source)

  if not no_calib:
    yield ConfigDACCmd(chip, \
                       tile, \
                       slce, \
                       value=value, \
                       inv=inv, \
                       out_range=rng,
                       source=source)


def gen_get_adc_status(circ,block,locstr):
  chip,tile,slce,_ =gen_unpack_loc(circ,locstr)
  return GetADCStatusCmd(chip,
                                  tile,
                                  slce)


def gen_get_integrator_status(circ,block,locstr):
  chip,tile,slce,_ =gen_unpack_loc(circ,locstr)
  return GetIntegStatusCmd(chip,
                                 tile,
                                 slce)


def gen_use_integrator(circ,block,locstr,config,debug=True,no_calib=False):
  chip,tile,slce,_ =gen_unpack_loc(circ,locstr)
  inv,= cast_enum([config.comp_mode],
                  [SignType])


  in_rng,out_rng = cast_enum(config.scale_mode,
                             [RangeType, \
                              RangeType])

  scf = config.scf('ic') if config.has_scf('ic') else 1.0
  init_cond = config.dac('ic')*scf
  init_cond = nearest_value(init_cond)

  yield UseIntegCmd(chip,
                    tile,
                    slce,
                    init_cond=init_cond,
                    inv=inv,
                    in_range=in_rng,
                    out_range=out_rng,
                    debug=debug)
  if not no_calib:
    yield ConfigIntegCmd(chip,
                         tile,
                         slce,
                         init_cond=init_cond,
                         inv=inv,
                         in_range=in_rng,
                         out_range=out_rng,
                         debug=debug)


def gen_use_multiplier(circ,block,locstr,config,no_calib=False):
  MODE_MAP = {"mul":False,'vga':True}

  chip,tile,slce,index =gen_unpack_loc(circ,locstr)
  use_coeff = MODE_MAP[config.comp_mode]
  if use_coeff:
    in0_rng,out_rng = cast_enum(config.scale_mode, \
                                [RangeType,RangeType])

    scf = config.scf('coeff') if config.has_scf('coeff') else 1.0
    coeff = config.dac('coeff')*scf
    coeff = nearest_value(coeff)
    yield UseMultCmd(chip,
                     tile,
                     slce,
                     index,
                     in0_range=in0_rng,
                     out_range=out_rng,
                     coeff=coeff,
                     use_coeff=True)

    if not no_calib:
      yield ConfigMultCmd(chip,
                          tile,
                          slce,
                          index,
                          in0_range=in0_rng,
                          out_range=out_rng,
                          coeff=coeff,
                          use_coeff=True)


  else:
    in0_rng,in1_rng,out_rng = cast_enum(config.scale_mode, \
                                [RangeType, \
                                 RangeType, \
                                 RangeType])

    yield UseMultCmd(chip,
                               tile,
                               slce,
                               index,
                               in0_range=in0_rng,
                               in1_range=in1_rng,
                               out_range=out_rng)

def gen_use_fanout(circ,block,locstr,config):
  chip,tile,slce,index =gen_unpack_loc(circ,locstr)
  inv0,inv1,inv2 = cast_enum(config.comp_mode,
                                    [SignType,
                                     SignType,
                                     SignType])
  in_rng, = cast_enum([config.scale_mode], [RangeType])

  yield UseFanoutCmd(chip,tile,slce,index,
                     in_range=in_rng,
                     inv0=inv0,
                     inv1=inv1,
                     inv2=inv2)


def is_same_tile(circ,loc1,loc2):
  inds1 = circ.board.key_to_loc(loc1)
  inds2 = circ.board.key_to_loc(loc2)
  for i in range(0,3):
    if inds1[i] != inds2[i]:
      return False
  return True

def gen_block(gprog,circ,block,locstr,config,no_calib=False):
  if block.name == 'multiplier':
    generator = gen_use_multiplier(circ,block,locstr,config,no_calib=no_calib)

  elif block.name == 'tile_dac':
    sources = list(circ.get_conns_by_dest(block.name,locstr,'in'))
    assert(len(sources) <= 1)
    source = DACSourceType.MEM
    if len(sources) == 1:
      sblk,sloc,sport = sources[0]
      assert(sblk == 'lut')
      assert(is_same_tile(circ,sloc,locstr))
      sliceno = circ.board.key_to_loc(sloc)[3]
      if sliceno == 0:
        source = DACSourceType.LUT0
      elif sliceno == 2:
        source = DACSourceType.LUT1
      else:
        raise Exception("unfamiliar slice: %s" % sliceno)

    generator = gen_use_dac(circ,block,locstr,config,source,no_calib=no_calib)

  elif block.name == 'tile_adc':
    sources = list(circ.get_conns_by_dest(block.name,locstr,'in'))
    generator = gen_use_adc(circ,block,locstr,config)
    cmd = gen_get_adc_status(circ,block,locstr)
    gprog.add(cmd)

  elif block.name == 'lut':
    sources = list(circ.get_conns_by_dest(block.name,locstr,'in'))
    assert(len(sources) == 1)
    sblk,sloc,sport = sources[0]
    assert(sblk == 'tile_adc')
    assert(is_same_tile(circ,sloc,locstr))
    sliceno = circ.board.key_to_loc(sloc)[3]
    if sliceno == 0:
      source = LUTSourceType.ADC0
    elif sliceno == 2:
      source = LUTSourceType.ADC1
    else:
      raise Exception("unfamiliar slice: %s" % sliceno)

    generator = gen_use_lut(circ,block,locstr,config,source)

  elif block.name == 'integrator':
    generator = gen_use_integrator(circ,block,locstr,config, \
                                   debug=True,no_calib=no_calib)
    cmd = gen_get_integrator_status(circ,block,locstr)
    gprog.add(cmd)

  elif block.name == 'fanout':
    generator = gen_use_fanout(circ,block,locstr,config)

  elif block.name == 'ext_chip_in' or \
       block.name == 'tile_in' or \
       block.name == 'chip_in' or \
       block.name == 'ext_chip_out' or \
       block.name == 'tile_out' or \
       block.name == 'chip_out':
    return

  else:
    raise Exception("unimplemented: <%s>" % block.name)

  for cmd in generator:
    gprog.add(cmd)

def gen_conn(gprog,circ,sblk,slocstr,sport,dblk,dlocstr,dport):
  TO_BLOCK_TYPE = {
    'lut': 'lut',
    'integrator': 'integ',
    'fanout': 'fanout',
    'tile_out': 'tile_output',
    'tile_in': 'tile_input',
    'tile_dac': 'dac',
    'tile_adc': 'adc',
    'multiplier':'mult',
    'ext_chip_in': 'chip_input',
    'ext_chip_out': 'chip_output',
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

  # these connections are not analog
  if sblk == 'lut' and dblk == 'tile_dac':
    return
  if sblk == 'tile_adc' and dblk == 'lut':
    return

  chip,tile,slce,index =gen_unpack_loc(circ,slocstr)
  src_port = TO_PORT_ID[sport]
  src_loc = CircPortLoc(chip,tile,slce,src_port,index=index)
  src_blk = TO_BLOCK_TYPE[sblk]

  chip,tile,slce,index =gen_unpack_loc(circ,dlocstr)
  dest_port = TO_PORT_ID[dport]
  dest_loc = CircPortLoc(chip,tile,slce,dest_port,index=index)
  dest_blk = TO_BLOCK_TYPE[dblk]

  cmd = MakeConnCmd(src_blk, \
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
    _,waveform = op.to_python(menv.input(config.label('in')))
    periodic = menv.is_periodic(config.label('in'))
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
  scaled_tc_hz = board.time_constant*conc_circ.tau
  scaled_sim_time = mathenv.sim_time/scaled_tc_hz
  scaled_input_time = mathenv.input_time/scaled_tc_hz
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
      gren.add(parse('micro_use_ard_adc %d' % out_no))

  for handle,info in dacs_in_use.items():
    in_no = hwenv.dac(handle)
    gren.add(parse('micro_use_ard_dac %d %s' % \
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
                    scaled_tc_hz,
                    info['scf']
                   )
    ))

def execconfig(path_handler,gren,board,conc_circ,menv,hwenv,filename,trialno):
  if hwenv.use_oscilloscope and len(hwenv.oscilloscope.outputs()) > 0:
    gren.add(parse('osc_setup_trigger'))
  gren.add(parse('micro_run'))
  circ_bmark,circ_indices,circ_scale_index,circ_opt,_,_ = \
                    path_handler.grendel_file_to_args(filename)



  adcs_in_use = get_ext_adcs_in_use(board,conc_circ,menv)
  for handle, info in adcs_in_use.items():
    out_no = hwenv.adc(handle)
    filename = path_handler.measured_waveform_file(circ_bmark, \
                                                   circ_indices, \
                                                   circ_scale_index, \
                                                   circ_opt,
                                                   menv.name, \
                                                   hwenv.name, \
                                                   info['label'],
                                                   trialno)
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


def postconfig(path_handler,gren,board,conc_circ,menv,hwenv,filename,ntrials):
  gren.add(parse('micro_setup_chip'))
  gren.add(parse('micro_get_status'))
  for trial in range(0,ntrials):
    execconfig(path_handler,gren,board,conc_circ,menv,hwenv,filename,trial)

  gren.add(parse('micro_get_status'))
  gren.add(parse('micro_teardown_chip'))
  return gren

def generate(paths,board,conc_circ,menv,hwenv,filename,ntrials):
  gren = GrendelProg()
  preamble(gren,board,conc_circ,menv,hwenv)
  no_calib = True
  #for block_name,loc,config in conc_circ.instances():
  #  if block_name == 'lut' or block_name == 'tile_adc':
  #    no_calib = True

  for block_name,loc,config in conc_circ.instances():
    block = conc_circ.board.block(block_name)
    gen_block(gren,conc_circ,block,loc,config,no_calib=no_calib)

  for sblk,sloc,sport, \
      dblk,dloc,dport in conc_circ.conns():
    gen_conn(gren,conc_circ,sblk,sloc,sport, \
             dblk,dloc,dport)

  postconfig(paths,gren,board,conc_circ,menv,hwenv,filename,ntrials)
  return gren
