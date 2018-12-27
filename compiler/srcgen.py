import lab_bench.lib.chip_command as chip_cmd
import lab_bench.lib.exp_command as exp_cmd
import lab_bench.lib.command as toplevel_cmd

class GrendelProg:

  def __init__(self):
    self._stmts = []

  def validate(self,cmd):
    cmdstr = str(cmd)
    args = cmdstr.split()
    assert(cmd.__class__.name() == args[0])
    test = cmd.__class__.parse(args[1:])
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

def gen_use_integrator(circ,block,locstr,config):
  INV_MAP = {'pos':False,'neg':True}

  chip,tile,slce,_ =gen_unpack_loc(circ,locstr)
  inv = INV_MAP[config.scale_mode[2]]
  init_cond = config.dac('ic')
  return chip_cmd.UseIntegCmd(chip,
                                 tile,
                                 slce,
                                 init_cond=init_cond,
                                 inv=inv)


def gen_use_multiplier(circ,block,locstr,config):
  MODE_MAP = {"default":False,'vga':True}

  chip,tile,slce,index =gen_unpack_loc(circ,locstr)
  use_coeff = MODE_MAP[config.mode]
  if use_coeff:
    coeff = config.dac('coeff')
    return chip_cmd.UseMultCmd(chip,
                               tile,
                               slce,
                               index,
                               coeff=coeff,
                               use_coeff=True)

  else:
    return chip_cmd.UseMultCmd(chip,
                                  tile,
                                  slce,
                                  index)

def gen_use_fanout(circ,block,locstr,config):
  INV_MAP = {'pos':False,'neg':True}

  chip,tile,slce,index =gen_unpack_loc(circ,locstr)
  inv0 = INV_MAP[config.scale_mode[0]]
  inv1 = INV_MAP[config.scale_mode[1]]
  inv2 = INV_MAP[config.scale_mode[2]]
  return chip_cmd.UseFanoutCmd(chip,tile,slce,index,
                               inv0=inv0,
                               inv1=inv1,
                               inv2=inv2)


def gen_block(gprog,circ,block,locstr,config):
  if block.name == 'multiplier':
    cmd = gen_use_multiplier(circ,block,locstr,config)
    gprog.add(cmd)

  elif block.name == 'integrator':
    cmd = gen_use_integrator(circ,block,locstr,config)
    gprog.add(cmd)

  elif block.name == 'fanout':
    cmd = gen_use_fanout(circ,block,locstr,config)
    gprog.add(cmd)

  elif block.name == 'due_adc' or \
       block.name == 'tile_in' or \
       block.name == 'tile_out':
    return

  else:
    raise Exception("unimplemented: <%s>" % block.name)

def gen_conn(gprog,circ,sblk,slocstr,sport,dblk,dlocstr,dport):
  TO_BLOCK_TYPE = {
    'dac': 'dac',
    'integrator': 'integ',
    'fanout': 'fanout',
    'tile_out': 'tile_output',
    'multiplier':'mult',
    'due_adc': 'chip_output'
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
  return cmd

def preamble(gren):
  gren.add(parse('reset'))
  gren.add(parse('set_volt_ranges differential -1.5 2.5 -1.5 2.5'))
  gren.add(parse('set_sim_time 0.20 0.01'))
  gren.add(parse('get_num_adc_samples'))
  gren.add(parse('get_num_dac_samples'))
  gren.add(parse('get_time_between_samples'))
  gren.add(parse('use_osc'))
  #FIXME `use_due_dac` if there are external inputs
  #FIXME `use_due_adc` / `use_osc` if there are external outputs
  gren.add(parse('compute_offsets'))
  gren.add(parse('use_chip'))

def postconfig(gren):
  gren.add(parse('run'))

def generate(board,conc_circ):
  gren = GrendelProg()
  preamble(gren)
  for block_name,loc,config in conc_circ.instances():
    block = conc_circ.board.block(block_name)
    gen_block(gren,conc_circ,block,loc,config)

  for sblk,sloc,sport, \
      dblk,dloc,dport in conc_circ.conns():
    gen_conn(gren,conc_circ,sblk,sloc,sport, \
             dblk,dloc,dport)
    print(sblk,sloc,sport,dblk,dloc,dport)

  postconfig(gren)
  return gren
