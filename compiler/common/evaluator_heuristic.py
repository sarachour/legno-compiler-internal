
def get_iface_ports(circuit):
  ports = []
  for block_name,loc,config in circuit.instances():
    if not circuit.board.handle_by_inst(block_name,loc) \
       is None:
      block = circuit.board.block(block_name)
      for out in block.outputs:
        ports.append((block_name,loc,out))
  return ports


def get_integrator_ports(circuit):
  ports = []
  for block_name,loc,config in circuit.instances():
    block = circuit.board.block(block_name)
    if block_name != "integrator":
      continue
    ports.append((block_name,loc,'in'))

  return ports

def get_ports(circuit):
  return get_integrator_ports(circuit) + get_iface_ports(circuit)
