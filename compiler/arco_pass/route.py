from chip.block import Block,BlockType
from chip.config import  Config
import chip.abs as acirc
import chip.conc as ccirc
import sys
import itertools
import logging
import compiler.arco_pass.util as arco_util
logger = logging.getLogger('arco_route')
logger.setLevel(logging.ERROR)

class RouteGraph:
    class RNode:
        ID = 0;

        def __init__(self,graph,block,loc,fragment=None):
            self._graph = graph
            self._loc = loc
            self._block = block
            self._inputs = graph.board.block(block).inputs
            self._outputs = graph.board.block(block).outputs
            self._passthrough = (graph.board.block(block).type == BlockType.BUS)
            self.id = RouteGraph.RNode.ID
            RouteGraph.RNode.ID += 1
            self._config = None
            self._fragment = fragment

        def clear(self):
            self._fragment = None
            self._config = None

        def set_config(self,c):
            assert(not c is None)
            self._config = c


        def set_fragment(self,f):
            assert(f is None or isinstance(f, acirc.ANode))
            if not self._fragment is None and f.id != self._fragment.id:
                r = "new: %s\n\n" % f.header()
                r += "old: %s\n\n" % self._fragment.header()
                raise Exception("fragment already assigned to <%s>\n\n%s" % (self,r))
            self._fragment = f

        @property
        def fragment(self):
            return self._fragment

        @property
        def config(self):
            if (self._config is None):
                raise Exception("no configuration: %s" % str(self))
            return self._config

        @property
        def loc(self):
            return self._loc

        @property
        def block_name(self):
            return self._block

        @staticmethod
        def to_key(block,loc):
            return "%s.%s" % (block,loc)


        @property
        def key(self):
            return RouteGraph.RNode.to_key(self._block,self._loc)

        def input_key(self,inp):
            return "I.%s.%s" % (self.key,inp)

        def output_key(self,out):
            return "O.%s.%s" % (self.key,out)


        def input_keys(self):
            for inp in self._inputs:
                yield self.input_key(inp)

        def output_keys(self):
            for out in self._outputs:
                yield self.output_key(out)

        def __repr__(self):
            fragstr = self._fragment.id if not self._fragment is None else "none"
            return "%d.%s%s [%s]" % (self.id,self._block,self._loc,fragstr)

    def __init__(self,board,cutoff,max_failures,max_resolutions):
        self._nodes = {}
        self._nodes_by_block = {}
        self.board = board
        self.cutoff = cutoff
        self.try_search = arco_util.TryObject("search",n_succ=None,n_fail=max_failures)
        self.try_resolve = arco_util.TryObject("rslv",n_succ=None,n_fail=max_resolutions)

    def add_node(self,block_name,loc):
        assert(isinstance(loc,str))
        node = RouteGraph.RNode(self,block_name,loc)
        if not block_name in self._nodes_by_block:
            self._nodes_by_block[block_name] = []

        self._nodes_by_block[block_name].append(node.key)
        self._nodes[node.key] = node

    def clear(self):
        for node in self._nodes.values():
            node.clear()

    def get_node(self,block_name,loc):
        node = RouteGraph.RNode(self,block_name,loc)
        if not node.key in self._nodes:
            for key in self._nodes.keys():
                logger.info(key)
            raise Exception("no node <%s>" % node.key)
        return self._nodes[node.key]

    def nodes_of_block(self,block_name,used=[]):
        used_keys = list(map(lambda node: node.key, used))
        for node_key in self._nodes_by_block[block_name]:
            node = self._nodes[node_key]
            if not node.key in used_keys:
                yield node



GRAPHS = {}
def build_instance_graph(board,cutoff,max_failures,max_resolutions):
    if board.name in GRAPHS:
        return GRAPHS[board.name]

    graph = RouteGraph(board,
                       max_failures=max_failures,
                       max_resolutions=max_resolutions,
                       cutoff=cutoff)

    for block,loc,metadata in board.instances():
        graph.add_node(block,loc)

    GRAPHS[board.name] = graph
    return graph

class DFSAction:
    def __init__(self):
        pass

    def apply(self,ctx):
        raise NotImplementedError

class RouteDFSContext:

    def __init__(self,state):
        self._state = state
        self._block_to_nodes = {}
        self._node_to_fragid = {}
        self._fragid_to_node = {}
        self._conns = {}
        self._resolved = []

    def get_node_by_fragment(self,frag):
        if not (frag.namespace,frag.id) in self._fragid_to_node:
            return None

        return self._fragid_to_node[(frag.namespace,frag.id)]


    def resolve_constraint(self,sn,sp,dn,dp):
        key = "%s.%s.%s->%s.%s.%s" % (sn.namespace,sn.id,sp,
                                      dn.namespace,dn.id,dp)
        assert(not key in self._resolved)
        self._resolved.append(key)

    def unresolved_constraints(self):
        for sn,sp,dn,dp in self._state.constraints():
            key = "%s.%s.%s->%s.%s.%s" % (sn.namespace,sn.id,sp, \
                                          dn.namespace,dn.id,dp)
            if not key in self._resolved:
                yield (sn,sp,dn,dp)


    def nodes(self):
        for block in self._block_to_nodes:
            for node in self._block_to_nodes[block].values():
                yield node

    def conns(self):
        for n1,p1,n2,p2 in self._conns.values():
            yield n1,p1,n2,p2

    def nodes_of_block(self,block):
        if not block in self._block_to_nodes:
            return []

        return self._block_to_nodes[block].values()

    @property
    def frag_ids(self):
        return self._fragid_to_node.keys()


    def in_use(self,board,block_name,loc):
        if not block_name in self._block_to_nodes:
            return False
        for node in self._block_to_nodes[block_name]:
            if node.loc == loc:
                return True

        return False

    def unused_node(self, block_name,loc,fragment=None):
        if not fragment is None:
            if (fragment.namespace,fragment.id) in \
               self._fragid_to_node:
                return False

        if not block_name in self._block_to_nodes:
            return True

        if RouteGraph.RNode.to_key(block_name,loc) in \
           self._block_to_nodes[block_name]:
            return False

        return True

    def use_node(self,node,config,fragment):
        # routing node
        if not self.unused_node(node.block_name,node.loc,fragment):
            raise Exception("node is already in context")

        assert(self.unused_node(node.block_name,node.loc))
        for other_node in self._fragid_to_node.values():
            if other_node.block_name == node.block_name \
               and other_node.loc == node.loc:
                raise Exception("node already mapped to another fragment")

        node.set_config(config)
        node.set_fragment(fragment)
        # fragment id
        if not fragment is None:
            self._fragid_to_node[(fragment.namespace,fragment.id)] = node
            self._node_to_fragid[node.key] = (fragment.namespace,fragment.id)

        if not node.block_name in self._block_to_nodes:
            self._block_to_nodes[node.block_name] = {}

        assert(not node.key in self._block_to_nodes)
        self._block_to_nodes[node.block_name][node.key] = node


    def conn_node(self,node1,port1,node2,port2):
        #assert(self._block_to_nodes[node1.block_name][node1.key].id == node1.id)
        #assert(self._block_to_nodes[node2.block_name][node2.key].id == node2.id)

        if (node1.output_key(port1) in self._conns):
            old_node1,old_port1,old_node2,old_port2 = \
                                    self._conns[node1.output_key(port1)]
            if old_node2.id == node2.id and old_port2 == port2:
                return

            r = "new-src:  %s.%s [%s]\n" % (node1,port1,node1.output_key(port1))
            r += "new-dest: %s.%s\n" % (node2,port2)
            r += "old-src:  %s.%s [%s]\n" % (old_node1,old_port1,old_node1.output_key(old_port1))
            r += "old-dest: %s.%s\n" % (old_node2,old_port2)
            raise Exception("<%s,%s> already connected.\n\n%s" % (node1,port1,r))
        self._conns[node1.output_key(port1)] = (node1,port1,node2,port2)


class DFSResolveConstraint(DFSAction):

    def __init__(self,snode,sport,dnode,dport):
        DFSAction.__init__(self)
        assert(isinstance(sport,str))
        assert(isinstance(dport,str))
        assert(isinstance(snode,acirc.ABlockInst))
        assert(isinstance(dnode,acirc.ABlockInst))
        assert(sport in snode.block.outputs)
        assert(dport in dnode.block.inputs)
        self._src_node = snode
        self._dst_node = dnode
        self._src_port = sport
        self._dst_port = dport


    def apply(self,ctx):
        ctx.resolve_constraint(self._src_node,self._src_port, \
                               self._dst_node,self._dst_port)

    def __repr__(self):
        return "rslv %s.%s -> %s.%s" % (self._src_node.name,self._src_port,
                                        self._dst_node.name,self._dst_port)



class DFSUseNode(DFSAction):

    def __init__(self,node,fragment,config):
        assert(not isinstance(fragment,int))
        DFSAction.__init__(self)
        self._frag  = fragment
        self._node = node
        assert(not config is None)
        self._config = config


    def apply(self,ctx):
        ctx.use_node(self._node,self._config,self._frag)

    def __repr__(self):
        if self._frag is None:
            return "%s [null]" % self._node

        if self._frag.id is None:
            raise Exception("fragment has no id <%s>" % self._frag)

        return "use %s [%d]" % (self._node,self._frag.id)

class DFSConnNode(DFSAction):

    def __init__(self,node1,port1,node2,port2):
        self._n1 = node1
        self._n2 = node2
        self._p1 = port1
        self._p2 = port2

    def apply(self,ctx):
        ctx.conn_node(self._n1,self._p1,self._n2,self._p2)

    def __repr__(self):
        return "conn (%s.%s)->(%s.%s)" % (self._n1,self._p1,self._n2,self._p2)

class DFSState:
    def __init__(self):
        self._stack = []
        self._frame = []
        self._ctx = None

    def make_new(self):
        return DFSState()

    def destroy(self):
        self._frame = []

    def copy(self):
        newstate = self.make_new()
        for frame in self._stack:
            newstate._stack.append(list(frame))

        return newstate

    def add(self,v):
        assert(isinstance(v,DFSAction))
        self._frame.append(v)

    def commit(self):
        if len(self._frame) > 0:
            self._stack.append(self._frame)
        self._frame = []

    def clear(self):
        self._stack = []
        self._frame = []
        self._ctx = None

    def pop(self):
        self._stack = self._stack[:-1]

    def new_ctx(self):
        raise NotImplementedError

    def context(self):
        ctx = self.new_ctx()
        idx = 0
        try:
            for frame in self._stack:
                for op in frame:
                    op.apply(ctx)
                    idx += 1

        except Exception as e:
            j = 0
            print("////////")
            for frame in self._stack:
                for op in frame:
                    if j < idx:
                        print(op)
                    elif j == idx:
                        print("[[%s]]" % op)
                    j += 1
                print("-----")
            raise e

        return ctx

    def __repr__(self):
        rep = "/////////////"
        for frame in self._stack:
            for op in frame:
                rep += str(op) + "\n"
            rep += "-----\n"
        rep += "/////////////"
        return rep



class RouteDFSState(DFSState):

    def __init__(self,fragment_map,cstrs):
        DFSState.__init__(self)
        self._fragments = fragment_map
        idents = []
        self._cstrs = []
        for sn,sp,dn,dp in cstrs:
            key = "%s.%d.%s->%s.%d.%s" % (sn.namespace,sn.id,sp,\
                                          dn.namespace,dn.id,dp)
            if not key in idents:
                idents.append(key)
                self._cstrs.append((sn,sp,dn,dp))


    def make_new(self):
        return RouteDFSState(self._fragments,self._cstrs)


    def new_ctx(self):
        return RouteDFSContext(self)


    def constraints(self):
        return self._cstrs

    def relevent_constraints(self,fragment):
        for sn,sp,dn,dp in self._cstrs:
            if sn.id == fragment.id or dn.id == fragment.id:
                yield (sn,sp,dn,dp)



def tac_collect_sources(graph,namespace,frag,port):
    sources = []
    if isinstance(frag,acirc.AInput):
        if frag.source is None:
            raise Exception("input isn't routed: <%s>" % frag)
        srcfrag,srcport = frag.source
        sources += tac_collect_sources(graph,namespace,srcfrag,srcport)

    elif isinstance(frag,acirc.AJoin):
        for parent in frag.parents():
            assert(isinstance(parent,acirc.AConn))
            srcfrag,srcport = parent.source
            if isinstance(srcfrag,acirc.ABlockInst):
                sources.append((srcfrag,srcport))
            elif isinstance(srcfrag,acirc.AJoin):
                sources += tac_collect_sources(graph,
                                               namespace,
                                               srcfrag,
                                               srcport)

            else:
                logger.info(srcfrag)
                raise NotImplementedError

    elif isinstance(frag,acirc.ABlockInst):
        sources.append((frag,port))

    else:
        raise NotImplementedError

    return sources



def create_instance_set_identifier(route):
    if len(route) == 0:
        return "@",[]

    ident_arr = list(set(map(lambda args: "%s:%s:%s" % args, route)))
    ident_arr.sort()
    raise NotImplementedError


def tac_abs_input(graph,namespace,fragment,ctx):
    assert(not fragment.source is None)
    new_frag,output = fragment.source
    new_namespace = fragment.label
    for new_ctx in traverse_abs_circuit(graph,
                                        new_namespace,
                                        new_frag,
                                        ctx=ctx):
        yield new_ctx



def tac_abs_get_resolutions(graph,ctx):
    choice_list = []
    route_list = []
    node_list = []
    cstr_list = []
    # compute all the valid routes
    for cstr in ctx.context().unresolved_constraints():
        src_node,src_port, \
            dest_node,dest_port = cstr
        src_rnode = ctx.context().get_node_by_fragment(src_node)
        dest_rnode= ctx.context().get_node_by_fragment(dest_node)
        if src_rnode is None or dest_rnode is None:
            continue

        paths= list(graph.board.find_routes(
                src_rnode.block_name,src_rnode.loc,src_port,
                dest_rnode.block_name,dest_rnode.loc,dest_port,
                cutoff=graph.cutoff
        ))
        all_routes = []
        n_choices = 1.0
        for path in paths:
            route = []
            for i in range(0,len(path)-1):
                sb,sl,sp = path[i]
                db,dl,dp = path[i+1]
                # internal connection
                if sb == db and sl == dl:
                    continue
                route += [(sb,sl,sp),(db,dl,dp)]
            all_routes.append(route)

        nodes = []
        routes = []
        for route in all_routes:
            new_nodes = set([(blk,loc) for blk,loc,port in route[1:-1]])
            valid = all(map(lambda args: ctx.context().unused_node(*args), new_nodes))
            if valid:
                nodes.append(new_nodes)
                routes.append(route)

        n_choices *= len(routes)
        choice_list.append(range(0,len(routes)))
        route_list.append(routes)
        node_list.append(nodes)
        cstr_list.append(cstr)


        if n_choices == 0:
            logger.warn("-> no valid routes exist")
            break

    for choices in itertools.product(*choice_list):
        nodes = []
        conns = []
        for idx in range(0,len(choices)):
            nodes += node_list[idx][choices[idx]]
            this_route = route_list[idx][choices[idx]]
            for i in range(0,len(this_route)-1):
                sb,sl,sp = this_route[i]
                db,dl,dp = this_route[i+1]
                # internal edge. ignore me
                if sb == db and sl == dl:
                    continue
                conns.append((this_route[i], this_route[i+1]))

        if arco_util.has_duplicates(nodes):
            logger.info("=== skipping ===")
            for node,cnts in arco_util.counts(nodes).items():
                logger.info("%s: %d" % (node,cnts))
            continue

        yield cstr_list,nodes,conns


def tac_abs_rslv_constraints(graph,ctx):
    for cstrs,intermediate_nodes,conns in \
        graph.try_resolve.iterate(tac_abs_get_resolutions(graph,ctx)):
        if len(cstrs) == 0:
            assert(len(intermediate_nodes) == 0)
            assert(len(conns) == 0)
            yield ctx
            return

        base_ctx=ctx.copy()
        for cstr in cstrs:
            step = DFSResolveConstraint(*cstr)
            base_ctx.add(step)

        for blk,loc in intermediate_nodes:
            node = RouteGraph.RNode(graph,blk,loc)
            logger.info("use %s" % (node))
            cfg = Config()
            cfg.set_comp_mode("*")
            step = DFSUseNode(node,
                              config=cfg, \
                              fragment=None)
            base_ctx.add(step)

        base_ctx.commit()
        logger.info("-- new conns --")
        for (sblk,sloc,sport),(dblk,dloc,dport) in conns:
            src_node = graph.get_node(sblk,sloc)
            dest_node = graph.get_node(dblk,dloc)
            logger.info("%s.%s -> %s.%s" % (src_node,sport,dest_node,dport))
            step = DFSConnNode(src_node,sport, \
                               dest_node,dport)
            base_ctx.add(step)

        base_ctx.commit()
        yield base_ctx


    graph.try_resolve.clear()

def tac_abs_block_inst(graph,namespace,fragment,ctx=None):
    node = ctx.context().get_node_by_fragment(fragment)
    if not node is None:
        yield ctx
        return

    used_nodes = ctx.context().nodes_of_block(fragment.block.name)
    free_nodes = list(graph.nodes_of_block(fragment.block.name,
                                           used=used_nodes))

    for node in free_nodes:
        base_ctx=ctx.copy()
        base_ctx.add(DFSUseNode(node,fragment,
                                    fragment.config))
        base_ctx.commit()
        for new_base_ctx in graph.try_search.iterate(tac_abs_rslv_constraints(graph, \
                                                                              ctx=base_ctx)):
            for new_ctx in tac_iterate_over_sources(graph,\
                                                    namespace,
                                                    new_base_ctx,
                                                    src_list=fragment.subnodes()):
                yield new_ctx

        #ctx.pop()


def tac_abs_conn(graph,namespace,fragment,ctx):
    for new_ctx in tac_iterate_over_sources(graph,namespace, \
                                            src_list=fragment.subnodes(),
                                            ctx=ctx):
        yield new_ctx

def tac_abs_join(graph,namespace,fragment,ctx):
    for new_ctx in tac_iterate_over_sources(graph,namespace, \
                                            ctx=ctx,\
                                            src_list=fragment.subnodes()):
        yield new_ctx

'''
resolve the join source to a node
'''

def tac_iterate_over_sources(graph,namespace,ctx, src_list):
    src_list = list(src_list)
    if len(src_list) == 0:
        yield ctx
    else:
        src_frag = src_list[0]
        for new_ctx in \
            graph.try_search.iterate(traverse_abs_circuit(graph,
                                                          namespace,
                                                          src_frag,
                                                          ctx=ctx)):
            for very_new_ctx in graph.try_search.iterate(tac_iterate_over_sources(graph,
                                                                                  namespace,
                                                                                  new_ctx,
                                                                                  src_list[1:])):
                yield very_new_ctx




def traverse_abs_circuit(graph,namespace,fragment,ctx=None):
    assert(isinstance(ctx,RouteDFSState))
    if isinstance(fragment,acirc.ABlockInst):
        for new_ctx in tac_abs_block_inst(graph,namespace,fragment,ctx):
            yield new_ctx

    elif isinstance(fragment,acirc.AConn):
        for new_ctx in tac_abs_conn(graph,namespace,fragment,ctx):
            yield new_ctx

    elif isinstance(fragment,acirc.AInput):
        for new_ctx in tac_abs_input(graph,namespace,fragment,ctx):
            yield new_ctx

    elif isinstance(fragment,acirc.AJoin):
        for new_ctx in tac_abs_join(graph,namespace,fragment,ctx):
            yield new_ctx

    else:
        raise Exception(fragment)

def der_abs_block_inst(fragment,ids):
    for node in fragment.subnodes():
        for cstr in derive_fragment_constraints(node,ids):
            yield cstr

def der_abs_input(fragment,ids):
    new_frag,output = fragment.source
    for cstr in derive_fragment_constraints(new_frag,ids):
        yield cstr

# TODO: remove all the namespacing, and instead use the internal
# fragment namespace
def der_abs_conn(fragment,ids,upstream=None):
    src_node,src_port = fragment.source
    dest_node,dest_port = fragment.dest
    assert(not src_node.namespace is None)
    assert(not dest_node.namespace is None)
    if isinstance(src_node,acirc.ABlockInst) and \
       isinstance(dest_node,acirc.ABlockInst):
        yield (src_node,src_port, \
               dest_node,dest_port)

        for subnode in fragment.subnodes():
            for cstr in derive_fragment_constraints(subnode,ids):
                yield cstr

    elif isinstance(src_node,acirc.AInput):
        rslv_src_node,rslv_src_port = src_node.source
        new_conn = acirc.AConn(rslv_src_node,rslv_src_port,
                               dest_node,dest_port)
        for result in der_abs_conn(new_conn, ids):
            yield result

    elif isinstance(src_node,acirc.AJoin):
        for subnode in src_node.subnodes():
            assert(isinstance(subnode,acirc.AConn))
            rslv_src_node,rslv_src_port = subnode.source
            new_conn = acirc.AConn(rslv_src_node,rslv_src_port,
                                   dest_node,dest_port)
            for cstr in der_abs_conn(new_conn,ids):
                yield cstr

    elif isinstance(dest_node,acirc.AJoin):
        if not dest_node.dest() is None:
            assert(isinstance(dest_node.dest(), acirc.AConn))
            rslv_dest_node,rslv_dest_port = dest_node.dest().dest
            new_conn = acirc.AConn(src_node,src_port,
                                rslv_dest_node,rslv_dest_port)
            for result in der_abs_conn(new_conn, ids):
                yield result
        else:
            pass
    else:
        raise Exception("implement conn: %s" % fragment)


def der_abs_join(fragment,ids,upstream=None):
    for subnode in fragment.subnodes():
        for cstr in derive_fragment_constraints(subnode,ids):
            yield cstr


def derive_fragment_constraints(fragment,ids):
    if fragment.id in ids:
        return

    ids.append(fragment.id)
    if isinstance(fragment,acirc.ABlockInst):
        for cstr in der_abs_block_inst(fragment,ids):
            yield cstr

    elif isinstance(fragment,acirc.AInput):
        for cstr in der_abs_input(fragment,ids):
            yield cstr


    elif isinstance(fragment,acirc.AConn):
        for cstr in der_abs_conn(fragment,ids):
            yield cstr

    elif isinstance(fragment,acirc.AJoin):
        for cstr in der_abs_join(fragment,ids):
            yield cstr
    else:
        raise Exception("unknown: %s" % fragment)

def derive_abs_circuit_constraints(fragment_map):

    for fragment in fragment_map.values():
        for sn,sp,dn,dp in derive_fragment_constraints(fragment,[]):
            assert(isinstance(sn,acirc.ABlockInst))
            assert(isinstance(dn,acirc.ABlockInst))
            yield (sn,sp,dn,dp)


def traverse_abs_circuits(graph,variables,fragment_map,ctx=None):
    variable = variables[0]
    fragment = fragment_map[variable]
    logger.info(">>> compute variable [%s] <<<" % variable)
    for result in \
        graph.try_search.iterate(traverse_abs_circuit(graph,variable,fragment,
                                                   ctx=ctx)):
        if len(variables) > 1:
            for subresult in graph.try_search.iterate(traverse_abs_circuits(graph,
                                                                            variables[1:],
                                                                            fragment_map,
                                                                            ctx=result)):
                yield subresult

        else:
            for new_result in \
                graph.try_search.iterate(tac_abs_rslv_constraints(graph,
                                                                  result)):
                unresolved = list(new_result.context().unresolved_constraints())
                total = len(new_result.constraints())
                if len(unresolved) > 0:
                    logger.info("-> skipping <%d/%d> unresolved configs" % \
                          (len(unresolved),total))
                    input("<continue>")
                    continue

                logger.info(">>> found solution [%d/%d unresolved] <<<" % (len(unresolved),\
                                                                   total))
                yield new_result

def build_concrete_circuit(graph,prob,fragment_map):
    variables = list(fragment_map.keys())
    for var,frag in fragment_map.items():
        logger.info("=== %s ===" % var)

    logger.info(">>> derive constraints <<<")
    all_cstrs = list(derive_abs_circuit_constraints(fragment_map))
    logger.info("# cstrs: %s" % len(all_cstrs))
    logger.info(">>> route circuit <<<")
    starting_ctx = RouteDFSState(fragment_map,all_cstrs)
    for idx,result in enumerate(traverse_abs_circuits(graph, \
                                                    variables, \
                                                    fragment_map,
                                                    ctx=starting_ctx)):
        state = result.context()
        circ = ccirc.ConcCirc(graph.board)

        for node in state.nodes():
            logger.info(node.block_name,node.loc)
            circ.use(node.block_name,node.loc,config=node.config)

        for n1,p1,n2,p2 in state.conns():
            circ.conn(n1.block_name,n1.loc,p1,
                      n2.block_name,n2.loc,p2)

        starting_ctx.clear()
        graph.clear()
        yield circ

    return

GRAPH = {}
def route(board,prob,node_map,cutoff=7,max_failures=None,max_resolutions=None):
    #sys.setrecursionlimit(1000)
    graph = build_instance_graph(board,
                                 cutoff=cutoff,
                                 max_failures=max_failures,
                                 max_resolutions=max_resolutions)
    logger.info('--- concrete circuit ---')
    for conc_circ in build_concrete_circuit(graph,prob,node_map):
        logger.info("<<<< CONCRETE CIRCUIT >>>>")
        yield conc_circ

    graph.try_search.clear()
