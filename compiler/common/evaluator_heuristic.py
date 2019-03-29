
def get_iface_ports(circuit,evaluate=False,weight=1.0):
  ports = []
  for block_name,loc,config in circuit.instances():
    if block_name == 'ext_chip_in':
      continue

    if not circuit.board.handle_by_inst(block_name,loc) \
       is None:
      block = circuit.board.block(block_name)
      for port in block.inputs:
        ports.append((weight,block_name,loc,port))
  return ports


def get_adc_ports(circuit,evaluate=False,weight=1.0):
  ports = []
  for block_name,loc,config in circuit.instances():
    block = circuit.board.block(block_name)
    if block_name != "adc":
      continue
    ports.append((weight,block_name,loc,'in'))
  return ports


def get_integrator_ports(circuit,evaluate=False,weight=1.0):
  ports = []
  for block_name,loc,config in circuit.instances():
    block = circuit.board.block(block_name)
    if block_name != "integrator":
      continue
    ports.append((weight,block_name,loc,'out'))
  return ports

def get_computation_ports(circuit,evaluate=False,weight=1.0):
  ports = []
  comp_ports = ['multiplier', 'adc']
  for block_name,loc,config in circuit.instances():
    block = circuit.board.block(block_name)
    if not block_name in comp_ports:
      continue

    for port in block.inputs + block.outputs:
      ports.append((weight,block_name,loc,port))

  return ports


def get_all_ports(circuit,evaluate=False,weight=1.0):
  ports = []
  for block_name,loc,config in circuit.instances():
    block = circuit.board.block(block_name)
    for port in block.inputs + block.outputs:
      ports.append((weight,block_name,loc,port))

  return ports


def get_ports(circuit,evaluate=False):
  n = len(get_computation_ports(circuit,evaluate,1.0))
  m = len(get_iface_ports(circuit,evaluate,1.0))

  if n + m > 1:
    return get_iface_ports(circuit,evaluate,1.0/(n+m))
  else:
    return get_iface_ports(circuit,evaluate,1.0)
