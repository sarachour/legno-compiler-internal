
def get_iface_ports(circuit,evaluate=False,weight=1.0):
  ports = []
  for block_name,loc,config in circuit.instances():
    if not circuit.board.handle_by_inst(block_name,loc) \
       is None:
      block = circuit.board.block(block_name)
      for out in block.outputs:
        ports.append((weight,block_name,loc,out))
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
    ports.append((weight,block_name,loc,'in'))
  return ports

def get_computation_ports(circuit,evaluate=False,weight=1.0):
  ports = []
  comp_ports = ['integrator', 'fanout', 'multiplier', \
                'adc', 'dac']
  for block_name,loc,config in circuit.instances():
    block = circuit.board.block(block_name)
    if not block_name in comp_ports:
      continue

    for port in block.inputs + block.outputs:
      ports.append((weight,weight,block_name,loc,port))

  return ports


def get_all_ports(circuit,evaluate=False):
  ports = []
  for block_name,loc,config in circuit.instances():
    block = circuit.board.block(block_name)
    for port in block.inputs + block.outputs:
      ports.append((block_name,loc,port))

  return ports

def get_ports(circuit,evaluate=False):
  n = len(get_integrator_ports(circuit,evaluate,1.0))

  return get_iface_ports(circuit,evaluate,1.0) + \
    get_integrator_ports(circuit,evaluate,1.0/n)
