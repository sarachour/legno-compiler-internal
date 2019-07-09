import chip.hcdc.hcdcv2_4 as hcdc
import chip.hcdc.globals as glb
import scripts.visualize.common as common

to_header = {
  'tile_out': 'tile out',
  'tile_in': 'tile in',
  'chip _in': 'chip in',
  'chip_out': 'chip out',
  'ext_chip_out': 'board out',
  'ext_chip_in': 'board in',
  'tile_dac':'dac',
  'tile_adc':'adc',
  'lut':'lut',
  'fanout': 'fanout',
  'multiplier': 'multiplier',
  'integrator': 'integrator',
}
to_type = {
  'tile_out': 'routing',
  'tile_in': 'routing',
  'chip_out': 'routing',
  'chip_in': 'routing',
  'ext_chip_out': 'routing',
  'ext_chip_in': 'routing',
  'tile_dac':'compute',
  'tile_adc':'compute',
  'lut':'compute',
  'fanout': 'copier',
  'multiplier': 'compute',
  'integrator': 'compute',
  'conns': 'connections',
}
to_expr = {
  ('multiplier','vga'): "$d_0 \cdot x_1$",
  ('multiplier','mul'): "$d_0 \cdot x_1$",
  ('integrator',None): "$z_0 = \int x_0, z_0(0) = d_0$",
  ('fanout',None): "z_i = x_0",
  ('lut',None): "$z_0 = f(d_0)$"
}

def count(iterator):
  x = 0
  for i in iterator:
    x += 1
  return x

def build_block_profile(block):
  n_comp_modes = len(block.comp_modes)
  scale_modes = {}
  subset = glb.HCDCSubset('unrestricted')
  block.subset(subset)
  for comp_mode in block.comp_modes:
    n_scale_modes = 0
    coeffs = []
    opranges = []
    for scm in block.scale_modes(comp_mode):
      if block.whitelist(comp_mode,scm):
        n_scale_modes += 1
        for port in block.outputs + block.inputs:
          for handle in list(block.handles(comp_mode,port)) \
              + [None]:

            coeffs.append(block.coeff(comp_mode, \
                                      scm, \
                                      port,
                                      handle))

            prop = block.props(comp_mode,scm,port,handle)
            opranges.append(prop.interval().bound)

    scale_modes[comp_mode] = {}
    scale_modes[comp_mode]['scale_modes'] = n_scale_modes
    scale_modes[comp_mode]['coeff_min'] = min(coeffs)
    scale_modes[comp_mode]['coeff_max'] = max(coeffs)
    scale_modes[comp_mode]['oprange_min'] = min(opranges)
    scale_modes[comp_mode]['oprange_max'] = max(opranges)

  cm = block.comp_modes[0]
  sm = block.scale_modes(cm)[0]

  inputs_analog = count(filter(lambda i: block.props(cm,sm,i).analog(), \
                      block.inputs))
  inputs_dig= count(filter(lambda i: not block.props(cm,sm,i).analog(), \
                      block.inputs))

  outputs_analog = count(filter(lambda o: block.props(cm,sm,o).analog(), \
                      block.outputs))
  outputs_dig= count(filter(lambda o: not block.props(cm,sm,o).analog(), \
                      block.outputs))

  return {
    'comp_modes': n_comp_modes,
    'scale_modes':scale_modes,
    'type':to_type[block.name] if block.name in to_type else None,
    'digital_inputs':inputs_analog,
    'analog_inputs':inputs_dig,
    'digital_outputs':outputs_analog,
    'analog_outputs':outputs_dig
  }

def build_circ_profile(board):
  profile = {'blocks':{}, 'conns':0}
  print("==== Build Block Profiles ====")
  for block in board.blocks:
    print(" -> %s" % block.name)
    block_profile = build_block_profile(block)
    block_profile['count'] = board.num_blocks(block.name)
    profile['blocks'][block.name] = block_profile

  print("==== Build Other Properties ====")
  profile['conns'] = count(board.connections())
  profile['time_constant'] = board.time_constant

  ext_inps = 0
  ext_outs = 0
  for h,b,l in board.handles():
    if b == 'ext_chip_out':
      ext_outs += 1
    elif b == 'ext_chip_analog_in':
      ext_inps += 1


  profile['ext_inputs'] = ext_inps
  profile['ext_outputs'] = ext_outs
  return profile

def build_board_summary(profile):
  desc = "board characteristics"
  table = common.Table('HDACv2 Board Characteristics', \
                       desc, 'hwboard','|ccc|cccc|ccc|ccc|ccc|',
                       benchmarks=False)
  fields = ['property', \
            'value']
  table.set_fields(fields)

  row = {}
  row['property'] = 'time constant'
  row['value'] = '%d hz' % profile['time_constant']
  table.data(None,row)

  row['property'] = 'connections'
  row['value'] = '%d' % profile['conns']
  table.data(None,row)

  row['property'] = 'external inputs'
  row['value'] = profile['ext_inputs']
  table.data(None,row)

  row['property'] = 'external outputs'
  row['value'] = profile['ext_outputs']
  table.data(None,row)
  table.write('hwboard.tbl')

def build_block_summary(profile):
  desc = "summaries of computational blocks available on device"
  table = common.Table('HDACv2 Board Block Summaries', \
                       desc, 'hwblocks','|ccc|cccc|ccc|ccc|ccc|',
                       benchmarks=False)
  fields = ['block', \
            'type', \
            'count', \
            'inputs', \
            'outputs', \
            'compute mode', \
            'function', \
            'scale modes', \
            'current limit', \
            'gain'
  ]

  table.set_fields(fields)
  for block in profile['blocks']:
    prof = profile['blocks'][block]

    if not block in to_header:
      continue

    row = {}
    row['block'] = "%s" % to_header[block]
    row['type'] = "%s" % prof['type']
    row['count'] = "%d" % prof['count']
    row['inputs'] = "%d / %d" % (prof['analog_inputs'], \
                                 prof['digital_inputs'])
    row['outputs'] = "%d / %d" % (prof['analog_outputs'], \
                                  prof['digital_outputs'])
    if block == 'multiplier':
      for comp_mode,data in prof['scale_modes'].items():
        row['compute mode'] = comp_mode
        row['function'] = to_expr[(block,comp_mode)]
        row['scale modes'] = data['scale_modes']
        row['current limit'] = "%d $\mu A$~ %d $\mu A$" \
                               % (data['oprange_min'], \
                                  data['oprange_max'])
        row['gain'] = "%d $\mu A$~ %d $\mu A$" \
                      % (data['coeff_min'], \
                         data['coeff_max'])

        table.data(None,row)

    else:
      comp_modes = list(prof['scale_modes'].keys())
      row['compute mode'] = "%d" % len(comp_modes)
      data = prof['scale_modes'][comp_modes[0]]
      row['scale_modes'] = data['scale_modes']
      if (block,None) in to_expr:
        row['function'] = to_expr[(block,None)]
      else:
        row['function'] = 'identity'

      row['scale modes'] = data['scale_modes']
      row['current limit'] = "%d $\mu A$~ %d $\mu A$" \
                              % (data['oprange_min'], \
                                data['oprange_max'])
      row['gain'] = "%d $\mu A$~ %d $\mu A$" \
                    % (data['coeff_min'], \
                        data['coeff_max'])
      table.data(None,row)
  table.write('hwblocks.tbl')


def visualize():
  print("==== Construct Board ====")
  board = hcdc.make_board()
  profile = build_circ_profile(board)
  build_block_summary(profile)
  build_board_summary(profile)

