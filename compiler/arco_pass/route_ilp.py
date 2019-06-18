import chip.abs as acirc
import chip.block as blocklib
import chip.conc as ccirc
import ops.ilpop as ilpop
import chip.config as configlib
import logging

logger = logging.getLogger('arco_route')
logger.setLevel(logging.DEBUG)

import networkx as nx

def get_sublayers(parent_layers):
  layers = []
  for parent_layer in parent_layers:
    layers += list(map(lambda i: parent_layer.layer(i), \
                       parent_layer.identifiers()))

  return layers

class RoutingEnv:

  def __init__(self,board,instances,connections,layers,assigns):
    self.board = board
    self.instances = instances
    self.connections = connections
    self.assigns = assigns
    self.layers = layers
    print("-> compute groups")
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
        if not (sblk,sport) in by_group[sgrp]['src']:
          by_group[sgrp]['src'][(sblk,sport)] = []

        by_group[sgrp]['src'][(sblk,sport)].append(sloc)

        if not (dblk,dport) in by_group[dgrp]['dest']:
          by_group[dgrp]['dest'][(dblk,dport)] = []

        by_group[dgrp]['dest'][(dblk,dport)].append(dloc)

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
          for (sblk,sport),slocs in by_group[group]['src'].items():
            for sloc in slocs:
              if board.route_exists(sblk,sloc,sport,\
                                    blk.name,loc,dport) \
                                    and not sblk in sinks:
                  sinks.append(sblk)
                  break

          #print("%s[%s].%s = %s" % (blk.name,group,dport,sinks))
          self.connectivities[(blk.name,group,dport)] = sinks

        for sport in blk.outputs:
          sources= []
          for (dblk,dport),dlocs in by_group[group]['dest'].items():
            for dloc in dlocs:
              if board.route_exists(blk.name,loc,sport,
                                    dblk,dloc,dport) \
                                    and not dblk in sources:
                sources.append(dblk)
                break;

          #print("%s[%s].%s = %s" % (blk.name,group,sport,sources))
          self.connectivities[(blk.name,group,sport)] = sources


  def loc_to_group(self,loc):
    matches = list(filter(lambda ch: ch.is_member(
      self.board.from_position_string(loc)
    ), self.layers))
    if not (len(matches) == 1):
      raise Exception("%s: <%d matches>" % (loc,len(matches)))
    return tuple(matches[0].position)

def ilp_instance_cstr(ilpenv,renv):
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

      instvar = ilpenv.decl(('inst',blk,frag_id,grp),
                            ilpop.ILPEnv.Type.BOOL)

      choices.append(instvar)
      if not (blk,grp) in by_block_group:
        by_block_group[(blk,grp)] = []
      by_block_group[(blk,grp)].append(instvar)

      if not loc is None:
        grp2 = renv.loc_to_group(loc)
        if grp == grp2:
          ilpenv.eq(ilpop.ILPVar(instvar), ilpop.ILPConst(1))
        else:
          ilpenv.eq(ilpop.ILPVar(instvar), ilpop.ILPConst(0))

    ilpenv.eq(
      ilpop.ILPMapAdd(
        list(map(lambda v: ilpop.ILPVar(v), choices))
      ),
      ilpop.ILPConst(1.0)
    )

  for (blk,grp),ilpvars in by_block_group.items():
    clauses = list(map(lambda v: ilpop.ILPVar(v), ilpvars))
    n = renv.counts[(grp,blk)]
    ilpenv.lte(ilpop.ILPMapAdd(clauses), ilpop.ILPConst(n))

def ilp_single_connection_cstr(ilpenv,renv,conn_id,conn,by_straddle):
  board = renv.board
  ((sblkname,sfragid),sport,(dblkname,dfragid),dport) = conn

  sblk = board.block(sblkname)
  dblk = board.block(dblkname)

  by_group = {}

  for grp1 in renv.groups:
    for grp2 in renv.groups:
      # this block fragment is constrained in a way where it can't be in this group
      if not ilpenv.has_ilpvar(('inst',sblkname,sfragid,grp1)):
        continue

      # this block fragment is constrained in a way where it can't be in this group
      if not ilpenv.has_ilpvar(('inst',dblkname,dfragid,grp2)):
        continue

      if not (grp1,grp2) in by_group \
         and grp1 != grp2:
        by_group[(grp1,grp2)] = []


  for cardkey,locs in renv.widths.items():
    (scblkname,sgrp,dcblkname,dgrp) = cardkey
    scblk = board.block(scblkname)
    dcblk = board.block(dcblkname)

    # this block fragment is constrained in a way where it can't be in this group
    if not ilpenv.has_ilpvar(('inst',sblkname,sfragid,sgrp)):
      continue

    # this block fragment is constrained in a way where it can't be in this group
    if not ilpenv.has_ilpvar(('inst',dblkname,dfragid,dgrp)):
      continue

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


    # this block is a computational block that is not the source block
    if scblk.type != blocklib.BlockType.BUS and \
        scblk.name != sblk.name:
      continue

    # this block is a computational block that is not the dest block
    if dcblk.type != blocklib.BlockType.BUS and \
        dcblk.name != dblk.name:
      continue

    connvar = ilpenv.decl(('conn',conn_id,cardkey),
                          ilpop.ILPEnv.Type.BOOL)

    by_group[(sgrp,dgrp)].append(connvar)

    if not cardkey in by_straddle:
      by_straddle[cardkey] = []

    by_straddle[cardkey].append(connvar)

  return by_group

def ilp_connection_cstr(ilpenv,renv):
  by_straddle = {}
  xgroups = []
  board = renv.board
  for conn_id,conn \
      in enumerate(renv.connections):

    by_group = ilp_single_connection_cstr(ilpenv,renv,conn_id,conn, \
                                          by_straddle=by_straddle)
    # add this straddlevar to the list of straddle vars
    ((sblkname,sfragid),sport,(dblkname,dfragid),dport) = conn

    for (sgrp,dgrp),group_conns in by_group.items():
      clause1 = ilpop.ILPAndVar(
        ilpenv,
        ilpop.ILPVar(ilpenv.get_ilpvar(('inst',sblkname,sfragid,sgrp))),
        ilpop.ILPVar(ilpenv.get_ilpvar(('inst',dblkname,dfragid,dgrp)))
      )
      if len(group_conns) > 0:
        xgroup = ilpenv.decl(('xgroup',conn_id,sgrp,dgrp), \
                             ilpop.ILPEnv.Type.BOOL)
        xgroups.append(xgroup)
        ilpenv.eq(
          ilpop.ILPMapAdd(
            list(map(lambda v: ilpop.ILPVar(v), group_conns))
          ),
          ilpop.ILPVar(xgroup)
        )
        ilpenv.eq(
            ilpop.ILPVar(clause1),
            ilpop.ILPVar(xgroup)
        );

      else:
        ilpenv.eq(
            ilpop.ILPVar(clause1),
            ilpop.ILPConst(0)
        )

  for cardkey,variables in by_straddle.items():
    cardinality = len(renv.widths[cardkey])
    ilpenv.lte(
      ilpop.ILPMapAdd(
        list(map(lambda v: ilpop.ILPVar(v), variables))
      ),
      ilpop.ILPConst(cardinality)
    );

  return xgroups

def hierarchical_route(board,locs,conns,layers,assigns):
  def get_n_conns(result):
    config = list(filter(lambda k: result[k] == 1, result.keys()))
    n_conns = len(list(filter(lambda k: 'conn' in k, config)))
    return n_conns


  print("-> generating environment")
  renv = RoutingEnv(board,locs,conns,layers, assigns)
  ilpenv = ilpop.ILPEnv()
  print("-> generating instance constraints")
  ilp_instance_cstr(ilpenv,renv)
  print("-> generating connection constraints")
  xlayers = ilp_connection_cstr(ilpenv,renv)

  ilpenv.set_objfun(
    ilpop.ILPMapAdd(
      list(map(lambda c: ilpop.ILPVar(c), xlayers))
    )
  )
  print("-> generate ilp")
  print("# vars: %d" % ilpenv.num_vars())
  print("# tempvars: %d" % ilpenv.num_tempvars())
  print("# cstrs: %d" % ilpenv.num_cstrs())
  ctx = ilpenv.to_model()
  print("-> solve problem")
  result = ctx.solve()
  if not ctx.optimal():
    return None

  config = list(filter(lambda k: result[k] == 1.0, result.keys()))
  n_conns = len(list(filter(lambda k: 'conn' in k, config)))
  print("n_conns: %s" % n_conns)
  assigns = {}
  for key in config:
    if 'inst' in key:
      _,blk,fragid,group = key
      assigns[(blk,fragid)] = group
      print("%s[%s] = %s" % (blk,fragid,group))

  return assigns

def random_locs(board,locs,conns,restrict):
  # test this annotation.
  def test_conns(assigns,blk,fragid,loc):
    for (sblk,sfragid),sport, \
        (dblk,dfragid),dport in conns:
      sloc,dloc = None,None
      if sblk == blk and fragid == sfragid:
        sloc = loc
      elif (sblk,sfragid) in assigns:
        sloc = assigns[(sblk,sfragid)]

      if dblk == blk and fragid == dfragid:
        dloc = loc
      elif (dblk,dfragid) in assigns:
        dloc = assigns[(dblk,dfragid)]

      if sloc is None or dloc is None:
        continue

      if not board.route_exists(sblk,sloc,sport, \
                                dblk,dloc,dport):
        print("cannot connect %s[%s].%s -> %s[%s].%s" % (sblk,sloc,sport,dblk,dloc,dport))
        return False
    return True

  def recurse(locs,assigns,in_use):
    if len(locs) == 0:
      yield assigns
    else:
      (blk,fragid),annot_loc = locs[0]
      if not annot_loc is None:
        new_assigns = dict(list(assigns.items()) + [((blk,fragid),annot_loc)])
        new_in_use = list(in_use) + [(blk,annot_loc)]
        for assign in recurse(locs[1:],new_assigns,new_in_use):
          yield assign

      else:
        orig_locs = list(filter(lambda loc: not (blk,loc) in in_use
                           and test_conns(assigns,blk,fragid,loc),
                           board.instances_of_block(blk)))

        print("%s[%d] = %d" % (blk,fragid,len(orig_locs)))

        if (blk,fragid) in restrict:
          prefix = restrict[(blk,fragid)]
          layer = board.sublayer(prefix[1:])
          valid_locs = list(filter(lambda loc: \
                                   layer.is_member(board.from_position_string(loc)),  \
                                   orig_locs))
          result_locs = valid_locs
        else:
          assert(len(locs) > 0)
          result_locs = orig_locs

        for loc in result_locs:
          new_assigns = dict(list(assigns.items()) + [((blk,fragid),loc)])
          new_in_use = list(in_use) + [(blk,loc)]
          for assign in recurse(locs[1:],new_assigns,new_in_use):
            yield assign

  for assigns in recurse(list(locs.items()), {}, []):
    result = {}
    for key,loc in assigns.items():
      result[key] = board.from_position_string(loc)
    yield result

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
      sloc = board.position_string(inst_assigns[(sblk,sfragid)])
      dloc = board.position_string(inst_assigns[(dblk,dfragid)])
      n_routes = 0
      for route in board.find_routes(sblk,sloc,sport,dblk,dloc,dport):
        double_use = list(filter(lambda place: place in in_use, route))
        if len(double_use) > 0:
          continue

        print("[%d] %s[%s].%s -> %s[%s].%s" % (len(remaining_conns), \
                                               sblk,sloc,sport,dblk,dloc,dport))
        n_routes += 1
        new_routes = list(routes)
        new_routes.append(to_conns(route))
        new_in_use = list(in_use) + route[1:-1]

        for solution in recurse(new_in_use, new_routes, remaining_conns[1:]):
          yield solution


  def sort_conns(conns):
    lengths = {}
    for conn in conns:
      (sblk,sfragid),sport,(dblk,dfragid),dport= conn
      sloc = board.position_string(inst_assigns[(sblk,sfragid)])
      dloc = board.position_string(inst_assigns[(dblk,dfragid)])
      for route in board.find_routes(sblk,sloc,sport,dblk,dloc,dport):
        lengths[conn] = len(route)
        break

      assert(conn in lengths)

    new_conns = sorted(conns, key=lambda c: -lengths[c])
    assert(len(new_conns) == len(conns))
    return new_conns

  new_conns = sort_conns(conns)
  for solution in recurse([],[],new_conns):
    yield solution


def make_concrete_circuit(board,routes,inst_assigns,configs):
  circ = ccirc.ConcCirc(board)
  for (blk,fragid),loc in inst_assigns.items():
    locstr = board.position_string(loc)
    circ.use(blk,locstr,configs[(blk,fragid)])

  for route in routes:
    for (sblk,sloc,sport),(dblk,dloc,dport) in route:
      if not circ.in_use(sblk,sloc):
        cfg = configlib.Config()
        cfg.set_comp_mode("*")
        circ.use(sblk,sloc,cfg)
      if not circ.in_use(dblk,dloc):
        cfg = configlib.Config()
        cfg.set_comp_mode("*")
        circ.use(dblk,dloc,cfg)

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

  print("=== tile resolution ===")
  chips = get_sublayers([board])
  tiles = get_sublayers(chips)
  chip_assigns = hierarchical_route(board,locs,conns,
                                   chips,{})

  tile_assigns = hierarchical_route(board,locs,conns,
                                    tiles,{})

  for assigns in random_locs(board,locs,conns,tile_assigns):
    for routes in find_routes(board,locs,conns,assigns):
      return make_concrete_circuit(board,routes,assigns,configs)
