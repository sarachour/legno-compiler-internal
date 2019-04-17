import chip.abs as acirc
import chip.block as blocklib
import chip.conc as ccirc
import ops.smtop as smtop
import logging

logger = logging.getLogger('arco_route')
logger.setLevel(logging.DEBUG)

import networkx as nx
class RoutingEnv:

  def __init__(self,board,instances,connections,parent_layers,assigns):
    self.board = board
    self.instances = instances
    self.connections = connections
    self.parent_layers = parent_layers
    self.assigns = assigns
    self.layers = []
    print("-> compute layers")
    for parent_layer in parent_layers:
      self.layers += list(map(lambda i: parent_layer.layer(i), \
                   parent_layer.identifiers()))

    self.groups = list(map(lambda layer: \
                    tuple(layer.position), self.layers))

    # compute possible connections.
    locmap = {}
    for locstr in set(map(lambda args: args[1], board.instances())):
      grp = self.loc_to_group(locstr)
      locmap[locstr] = grp

    print("-> compute connections")
    self.widths = {}
    by_group = dict(map(lambda g: (g,{'src':{},'dest':{}}), self.groups))
    for (sblk,sport),(dblk,dport),locs in board.connection_list():
      for sloc,dloc in filter(lambda args: \
                              locmap[args[0]] != locmap[args[1]], locs):
        sgrp = locmap[sloc]
        dgrp = locmap[dloc]
        key = (sblk,sgrp,dblk,dgrp)
        by_group[sgrp]['src'][(sblk,sport)] = sloc
        by_group[dgrp]['dest'][(dblk,dport)] = dloc

        if not key in self.widths:
          self.widths[key] = []
        if not dloc in self.widths[key]:
          self.widths[key].append((dloc))

    # compute quantities
    print("-> compute counts")
    self.counts = {}
    for layer in self.layers:
      group = tuple(layer.position)
      for blk in board.blocks:
        n = len(list(board.block_locs(layer,blk.name)))
        self.counts[(group,blk.name)] = n


    print("-> compute reachable")
    self.connectivities = {}
    for layer in self.layers:
      group = tuple(layer.position)
      for blk in board.blocks:
        if self.counts[(group,blk.name)] == 0:
          continue

        loc = list(board.block_locs(layer,blk.name))[0]
        for dport in blk.inputs:
          sinks = []
          for (sblk,sport),sloc in by_group[group]['src'].items():
            if board.route_exists(sblk,sloc,sport,\
                                  blk.name,loc,dport):
              if not dblk in sinks:
                sinks.append(sblk)


          self.connectivities[(blk.name,group,dport)] = sinks

        for sport in blk.outputs:
          sources= []
          for (dblk,dport),dloc in by_group[group]['dest'].items():
            if board.route_exists(blk.name,loc,sport,
                                  dblk,dloc,dport):
              if not dblk in sources:
                sources.append(dblk)


          self.connectivities[(blk.name,group,sport)] = sources


  def loc_to_group(self,loc):
    matches = list(filter(lambda ch: ch.is_member(
      self.board.from_position_string(loc)
    ), self.layers))
    if not (len(matches) == 1):
      raise Exception("%s: <%d matches>" % (loc,len(matches)))
    return tuple(matches[0].position)

def smt_instance_cstr(smtenv,renv):
  # create group-conn hot coding
  by_block_group = {}
  for (blk,frag_id),loc in renv.instances.items():
    choices = []
    if (blk,frag_id) in renv.assigns:
      prefix = renv.assigns[(blk,frag_id)]
      par_layer = renv.board.sublayer(prefix[1:])
    else:
      par_layer = None

    for grp in renv.groups:
      if not par_layer is None and \
         not par_layer.is_member(grp):
        continue

      if renv.counts[(grp,blk)] == 0:
        continue

      instvar = smtenv.decl(('inst',blk,frag_id,grp),
                        smtop.SMTEnv.Type.INT)

      choices.append(instvar)
      if not (blk,grp) in by_block_group:
        by_block_group[(blk,grp)] = []
      by_block_group[(blk,grp)].append(instvar)

      if not loc is None:
        grp2 = renv.loc_to_group(loc)
        if grp == grp2:
          smtenv.eq(smtop.SMTVar(instvar), smtop.SMTConst(1))
        else:
          smtenv.eq(smtop.SMTVar(instvar), smtop.SMTConst(0))

      else:
        smtenv.lte(smtop.SMTVar(instvar), smtop.SMTConst(1))
        smtenv.gte(smtop.SMTVar(instvar), smtop.SMTConst(0))

    smtenv.eq(
      smtop.SMTMapAdd(
        list(map(lambda v: smtop.SMTVar(v), choices))
      ),
      smtop.SMTConst(1.0)
    )

  for (blk,grp),smtvars in by_block_group.items():
    clauses = list(map(lambda v: smtop.SMTVar(v), smtvars))
    n = renv.counts[(grp,blk)]
    smtenv.lte(smtop.SMTMapAdd(clauses), smtop.SMTConst(n))

def smt_single_connection_cstr(smtenv,renv,conn_id,conn,by_straddle):
  board = renv.board
  ((sblkname,sfragid),sport,(dblkname,dfragid),dport) = conn

  sblk = board.block(sblkname)
  dblk = board.block(dblkname)

  by_group = {}

  for cardkey,locs in renv.widths.items():
    (scblkname,sgrp,dcblkname,dgrp) = cardkey
    scblk = board.block(scblkname)
    dcblk = board.block(dcblkname)

    # the source block does not exist in this group
    if not (sgrp,sblkname) in renv.counts or \
        renv.counts[(sgrp,sblkname)] == 0:
      continue

    # the dest block does not exist in this group
    if not (dgrp,dblkname) in renv.counts or \
        renv.counts[(dgrp,dblkname)] == 0:
      continue

    # the src block cannot be connected to this straddling edge
    if not dcblkname in renv.connectivities[(sblkname,sgrp,sport)]:
      continue

    # the dest block cannot be connect to this straddling edge
    if not scblkname in renv.connectivities[(dblkname,dgrp,dport)]:
      continue

    # this block fragment is constrained in a way where it can't be in this group
    if not smtenv.has_smtvar(('inst',sblkname,sfragid,sgrp)):
      continue

    # this block fragment is constrained in a way where it can't be in this group
    if not smtenv.has_smtvar(('inst',dblkname,dfragid,dgrp)):
      continue

    # this block is a computational block that is not the source block
    if scblk.type != blocklib.BlockType.BUS and \
        scblk.name != sblk.name:
      continue

    # this block is a computational block that is not the dest block
    if dcblk.type != blocklib.BlockType.BUS and \
        dcblk.name != dblk.name:
      continue

    connvar = smtenv.decl(('conn',conn_id,cardkey),
                      smtop.SMTEnv.Type.INT)
    smtenv.lte(smtop.SMTVar(connvar), smtop.SMTConst(1))
    smtenv.gte(smtop.SMTVar(connvar), smtop.SMTConst(0))

    if not (sgrp,dgrp) in by_group:
      by_group[(sgrp,dgrp)] = []

    by_group[(sgrp,dgrp)].append(connvar)

    if not cardkey in by_straddle:
      by_straddle[cardkey] = []

    by_straddle[cardkey].append(connvar)

  return by_group

def smt_connection_cstr(smtenv,renv):
  by_straddle = {}
  xgroups = []
  board = renv.board
  for conn_id,conn \
      in enumerate(renv.connections):

    by_group = smt_single_connection_cstr(smtenv,renv,conn_id,conn, \
                                          by_straddle=by_straddle)
    # add this straddlevar to the list of straddle vars
    ((sblkname,sfragid),sport,(dblkname,dfragid),dport) = conn

    for (sgrp,dgrp),group_conns in by_group.items():
      xgroup = smtenv.decl(('xgroup',conn_id,sgrp,dgrp), smtop.SMTEnv.Type.INT)
      smtenv.lte(smtop.SMTVar(xgroup), smtop.SMTConst(1))
      smtenv.gte(smtop.SMTVar(xgroup), smtop.SMTConst(0))

      xgroups.append(xgroup)
      smtenv.eq(
        smtop.SMTMapAdd(
          list(map(lambda v: smtop.SMTVar(v), group_conns))
        ),
        smtop.SMTVar(xgroup)
      )
      smtenv.cstr(
        smtop.SMTBidirImplies(
          smtop.SMTAnd(
            smtop.SMTEq(
              smtop.SMTVar(smtenv.get_smtvar(('inst',sblkname,sfragid,sgrp))),
              smtop.SMTConst(1)
            ),
            smtop.SMTEq(
              smtop.SMTVar(smtenv.get_smtvar(('inst',dblkname,dfragid,dgrp))),
              smtop.SMTConst(1)
            )
          ),
          smtop.SMTEq(
            smtop.SMTVar(xgroup),
            smtop.SMTConst(1)
          )
        )
      );


  for cardkey,variables in by_straddle.items():
    cardinality = len(renv.widths[cardkey])
    smtenv.lte(
      smtop.SMTMapAdd(
        list(map(lambda v: smtop.SMTVar(v), variables))
      ),
      smtop.SMTConst(cardinality)
    );

  return xgroups

def hierarchical_route(board,locs,conns,parent_layers,assigns):
  def get_n_conns(result):
    config = list(filter(lambda k: result[k] == 1, result.keys()))
    n_conns = len(list(filter(lambda k: 'conn' in k, config)))
    return n_conns

  def binary_search(ctx,nlow,nhi,result):
    if abs(nlow - nhi) < 2:
      return result

    n_next = ((nlow+nhi)/2)
    ctx.push()
    ctx.cstr(
      smtop.SMTLTE(
        smtop.SMTMapAdd(
          list(map(lambda c: smtop.SMTVar(c), xlayers))
        ),
        smtop.SMTConst(n_next)
      ).to_z3(ctx)
    )
    print("max-conns: %d" % n_next)
    new_result = ctx.solve()
    if not ctx.sat():
      ctx.pop()
      return binary_search(ctx,n_next,nhi,result)
    else:
      print("new-conns: %d" % get_n_conns(new_result))
      nhi = get_n_conns(new_result)
      return binary_search(ctx,nlow,nhi,new_result)

  print("-> generating environment")
  renv = RoutingEnv(board,locs,conns,parent_layers,assigns)
  smtenv = smtop.SMTEnv()
  print("-> generating problem")
  smt_instance_cstr(smtenv,renv)
  xlayers = smt_connection_cstr(smtenv,renv)
  print("-> generate z3")
  print("# vars: %d" % smtenv.num_vars())
  print("# cstrs: %d" % smtenv.num_cstrs())
  ctx = smtenv.to_z3()
  print("-> solve problem")
  result = ctx.solve()
  if not ctx.sat():
    return None

  result = binary_search(ctx,
                       0, \
                       get_n_conns(result),
                       result)

  config = list(filter(lambda k: result[k] == 1, result.keys()))
  n_conns = len(list(filter(lambda k: 'conn' in k, config)))
  print("n_conns: %s" % n_conns)
  assigns = {}
  for key in config:
    if 'inst' in key:
      _,blk,fragid,group = key
      assigns[(blk,fragid)] = group

  return renv.layers,assigns

def find_routes(board,locs,conns,inst_assigns):
  def to_conns(route):
    result = []
    for i in range(0,len(route)-1):
      sb,sl,sp = route[i]
      db,dl,dp = route[i+1]
      # internal connection
      if sb == db and sl == dl:
        continue
      result.append([(sb,sl,sp),(db,dl,dp)])
    return result

  def recurse(in_use,routes,remaining_conns):
    if len(remaining_conns) == 0:
      yield routes

    else:
      (sblk,sfragid),sport,(dblk,dfragid),dport = remaining_conns[0]
      print("[%d] %s[%s].%s -> %s[%s].%s" % (len(remaining_conns), sblk,sfragid,sport,dblk,dfragid,dport))
      sloc = board.position_string(inst_assigns[(sblk,sfragid)])
      dloc = board.position_string(inst_assigns[(dblk,dfragid)])
      for route in board.find_routes(sblk,sloc,sport,dblk,dloc,dport):
        double_use = list(filter(lambda place: place in in_use, route))
        if len(double_use) > 0:
          continue

        new_routes = list(routes)
        new_routes.append(to_conns(route))
        new_in_use = list(in_use) + route[0:-1]
        for solution in recurse(new_in_use, new_routes, remaining_conns[1:]):
          yield solution


  def sort_conns(conns):
    lengths = {}
    for conn in conns:
      (sblk,sfragid),sport,(dblk,dfragid),dport= conn
      sloc = board.position_string(inst_assigns[(sblk,sfragid)])
      dloc = board.position_string(inst_assigns[(dblk,dfragid)])
      print("%s[%s].%s -> %s[%s].%s" % (sblk,sloc,sport,dblk,dloc,dport))
      for route in board.find_routes(sblk,sloc,sport,dblk,dloc,dport):
        lengths[conn] = len(route)
        print(" -> %d" % len(route))
        break

    new_conns = sorted(conns, key=lambda c: -lengths[c])
    print(lengths[new_conns[0]])
    input()
    return new_conns

  new_conns = sort_conns(conns)
  for solution in recurse([],[],new_conns):
    yield solution
 

def make_concrete_circuit(board,routes,inst_assigns,configs):
  circ = ccirc.ConcCirc(board)
  for (blk,fragid),loc in inst_assigns.items():
    locstr = board.position_string(loc)
    circ.use(blk,locstr,configs[blk,fragid])

  for route in routes:
    for (sblk,sloc,sport),(dblk,dloc,dport) in route:
      if not circ.in_use(sblk,sloc):
        circ.use(sblk,sloc)
      if not circ.in_use(dblk,dloc):
        circ.use(dblk,dloc)

      circ.conn(sblk,sloc,sport,dblk,dloc,dport)

  return circ



# TODO: check if there exists a path through port before adding to cardinality.

def extract_src_node(fragment,port=None):
    if isinstance(fragment,acirc.ABlockInst):
      assert(not port is None)
      yield fragment,port

    elif isinstance(fragment,acirc.AConn):
      sb,sp = fragment.source
      db,dp = fragment.dest
      for block,port in extract_src_node(sb,port=sp):
        yield block,port

    elif isinstance(fragment,acirc.AInput):
      node,output = fragment.source
      for block,port in extract_src_node(node,port=output):
        yield block,port

    elif isinstance(fragment,acirc.AJoin):
      for ch in fragment.parents():
        for node,port in extract_src_node(ch):
          yield node,port

    else:
        raise Exception(fragment)

def extract_backward_paths(nodes,starting_node):
  conns = []
  for next_node in starting_node.parents():
    if isinstance(next_node,acirc.AConn):
      src_node,src_port_orig = next_node.source
      dest_block,dest_port = next_node.dest
      assert(isinstance(dest_block,acirc.ABlockInst))
      dest_key =(dest_block.block.name, dest_block.id)
      for src_block,src_port in \
          extract_src_node(src_node,port=src_port_orig):
        src_key = (src_block.block.name, src_block.id)
        conns.append((src_key,src_port, \
                      dest_key,dest_port))

  return conns


def route(board,prob,node_map):
  nodes = {}
  for k,v in node_map.items():
    for node in v.nodes():
      if isinstance(node,acirc.ABlockInst):
        key = (node.block.name,node.id)
        assert(not key in nodes)
        nodes[key] = node

  conns = []
  locs = {}
  configs = {}
  for key,node in nodes.items():
    conns += extract_backward_paths(nodes,node)
    locs[key] = node.loc
    configs[key] = node.config

  print("=== chip resolution ===")
  chips,chip_assigns = hierarchical_route(board,locs,conns,[board],{})
  print("=== tile resolution ===")
  tiles,tile_assigns = hierarchical_route(board,locs,conns, \
                                          chips,chip_assigns)
  print("=== slice resolution ===")
  slices,slice_assigns = hierarchical_route(board,locs,conns, \
                                            tiles,tile_assigns)

  print("=== left/right resolution ===")
  insts,inst_assigns = hierarchical_route(board,locs,conns, \
                                            slices,slice_assigns)


  print("=== finding routes ===")
  routes = None
  for routes in find_routes(board,locs,conns,inst_assigns):
    break;

  print("=== making concrete circuit ===")
  assert(not routes is None)
  return make_concrete_circuit(board,routes,inst_assigns,configs)
