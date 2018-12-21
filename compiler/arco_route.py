from chip.block import Block
import chip.abs as acirc
import chip.conc as ccirc
import sys
import itertools
import logging
logger = logging.getLogger('arco_route')
class RouteGraph:
    class RNode:

        def __init__(self,graph,block,loc):
            self._graph = graph
            self._loc = loc
            self._block = block
            self._inputs = graph.board.block(block).inputs
            self._outputs = graph.board.block(block).outputs
            self._passthrough = (graph.board.block(block).type == Block.BUS)
            self._config = None

        def set_config(self,c):
            assert(not c is None)
            self._config = c
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

        @property
        def key(self):
            return "%s.%s" % (self._block,self._loc)

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
            return "%s%s" % (self._block,self._loc)

    def __init__(self,board):
        self._nodes = {}
        self._nodes_by_block = {}
        self.board = board


    def add_node(self,block_name,loc):
        assert(isinstance(loc,str))
        node = RouteGraph.RNode(self,block_name,loc)
        if not block_name in self._nodes_by_block:
            self._nodes_by_block[block_name] = []

        self._nodes_by_block[block_name].append(node.key)
        self._nodes[node.key] = node

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
def build_instance_graph(board):
    if board.name in GRAPHS:
        return GRAPHS[board.name]

    graph = RouteGraph(board)
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

    def __init__(self):
        self._nodes_by_block = {}
        self._nodes_by_fragment_id = {}
        self._conns = {}


    def get_node_by_fragment(self,namespace,frag):
        if not (namespace,frag.id) in self._nodes_by_fragment_id:
            return None

        return self._nodes_by_fragment_id[(namespace,frag.id)]


    def nodes(self):
        for block in self._nodes_by_block:
            for node in self._nodes_by_block[block]:
                yield node

    def conns(self):
        for n1,p1,n2,p2 in self._conns.values():
            yield n1,p1,n2,p2

    def nodes_of_block(self,block):
        if not block in self._nodes_by_block:
            return []

        return self._nodes_by_block[block]

    @property
    def frag_ids(self):
        return self._nodes_by_fragment_id.keys()

    def in_use(self,board,block_name,loc):
        if not block_name in self._nodes_by_block:
            return False
        for node in self._nodes_by_block[block_name]:
            if node.loc == loc:
                return True

        return False


    def use_node(self,node,config,namespace,fragment):
        if (namespace,fragment.id) in self._nodes_by_fragment_id:
            raise Exception ("%s.%d already in context" % (namespace,fragment_id))

        node.set_config(config)
        self._nodes_by_fragment_id[(namespace,fragment.id)] = node
        if not node.block_name in self._nodes_by_block:
            self._nodes_by_block[node.block_name] = []

        self._nodes_by_block[node.block_name].append(node)

    def conn_node(self,node1,port1,node2,port2):
        if (node1.output_key(port1) in self._conns):
            _,_,old_node2,old_port2 = self._conns[node1.output_key(port1)]
            print("src:  %s.%s" % (node1,port1))
            print("new-dest: %s.%s" % (node2,port2))
            print("old-dest: %s.%s" % (old_node2,old_port2))
            raise Exception("<%s,%s> already connected." % (node1,port1))
        self._conns[node1.output_key(port1)] = (node1,port1,node2,port2)

    
class DFSUseNode(DFSAction):

    def __init__(self,node,namespace,frag,config):
        assert(not isinstance(frag,int))
        DFSAction.__init__(self)
        self._namespace = namespace
        self._frag  = frag
        self._node = node
        assert(not config is None)
        self._config = config


    def apply(self,ctx):
        ctx.use_node(self._node,self._config,self._namespace,self._frag)

    def __repr__(self):
        if self._frag.id is None:
            raise Exception("fragment has no id <%s>" % self._frag)
        return "%s [%s.%d]" % (self._node,self._namespace,self._frag.id)

class DFSConnNode(DFSAction):

    def __init__(self,node1,port1,node2,port2):
        self._n1 = node1
        self._n2 = node2
        self._p1 = port1
        self._p2 = port2

    def apply(self,ctx):
        ctx.conn_node(self._n1,self._p1,self._n2,self._p2)

    def __repr__(self):
        return "(%s.%s)->(%s.%s)" % (self._n1,self._p1,self._n2,self._p2)
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

    def pop(self):
        self._stack = self._stack[:-1]

    def new_ctx(self):
        raise NotImplementedError

    def context(self):
        ctx = self.new_ctx()

        for frame in self._stack:
            for op in frame:
                op.apply(ctx)

        return ctx

    def __repr__(self):
        rep = ""
        for frame in self._stack:
            for op in frame:
                rep += str(op) + "\n"
            rep += "-----\n"
        return rep



class RouteDFSState(DFSState):

    def __init__(self,fragment_map):
        DFSState.__init__(self)
        self._fragments = fragment_map

    def make_new(self):
        return RouteDFSState(self._fragments)


    def new_ctx(self):
        return RouteDFSContext()



def tac_iterate_over_sources(graph,namespace,ctx, src_list,cutoff=1):
        if len(src_list) == 0:
            yield ctx
        else:
            src_frag = src_list[0]
            for new_ctx in \
                traverse_abs_circuit(graph,
                                     namespace,
                                     src_frag,
                                     ctx=ctx,
                                     cutoff=cutoff):
                for very_new_ctx in tac_iterate_over_sources(graph,
                                                             namespace,
                                                             new_ctx,
                                                             src_list[1:],
                                                             cutoff):
                    yield very_new_ctx

def tac_abs_block_inst(graph,namespace,fragment,ctx=None,cutoff=1):
    node = ctx.context().get_node_by_fragment(
        namespace,fragment)

    if not node is None:
        yield ctx
        return

    used_nodes = ctx.context().nodes_of_block(fragment.block.name)
    free_nodes = list(graph.nodes_of_block(fragment.block.name,
                                           used=used_nodes))

    for node in free_nodes:
        base_ctx=ctx.copy()
        base_ctx.add(DFSUseNode(node,namespace,
                                    fragment,
                                    fragment.config))
        base_ctx.commit()
        for new_ctx in tac_iterate_over_sources(graph,namespace,base_ctx,
                                        list(fragment.parents()),
                                        cutoff):
            yield new_ctx

        #ctx.pop()


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

def tac_abs_conn(graph,namespace,fragment,ctx,cutoff):
    parents = list(fragment.parents())
    assert(len(parents) == 1)
    # find other edge
    srcfrag_start,srcport_start= fragment.source
    dstfrag,dstport = fragment.dest
    sources = tac_collect_sources(graph,namespace, \
                                  srcfrag_start, \
                                  srcport_start)

    logger.debug("[dst] block=%s, port=%s" % (dstfrag,dstport))

    curr_state = ctx.context()
    sources_locs = list(map(lambda arg:
                            list(graph.board.instances_of_block(
                                arg[0].block.name)),
                            sources))

    count = 0
    unusable_routes = []
    source_frags = list(map(lambda src: src[0], sources))
    source_ports = list(map(lambda src: src[1], sources))
    print("sources: %s" % str(sources))

    for endpt_ctx in tac_iterate_over_sources(graph,
                                              namespace,
                                              ctx,source_frags,
                                              cutoff):

        # compute nodes for endponts
        state = endpt_ctx.context()
        srcnodes = map(lambda srcfrag : \
                       state.get_node_by_fragment(namespace,srcfrag),
                       source_frags)
        dstnode = state.get_node_by_fragment(namespace,dstfrag)

        # compute all routes, given endpoints
        all_routes = []
        print("sources: %s" % str(sources))
        for srcnode,srcport in zip(srcnodes,source_ports):
            print(srcnode,srcport)
            print(dstnode,dstport)
            routes = list(graph.board.find_routes(
                srcnode.block_name,srcnode.loc,srcport,
                dstnode.block_name,dstnode.loc,dstport,
                cutoff=cutoff
            ))
            all_routes.append(routes)

        # compute all combinations of routes
        routes_by_inst_set = {}
        for route_coll in itertools.product(*all_routes):
            key,instcoll = create_instance_set_identifier(route_coll[0][1:-1])
            if key is None:
                continue

            if not key in routes_by_inst_set:
                routes_by_inst_set[key] = {'routesets':[],'instcoll':instcoll}
            routes_by_inst_set[key]['routesets'].append(route_coll[0])
            assert(len(instcoll) == 0)
        # add intermediate instances.
        for _,data in routes_by_inst_set.items():
            instances = data['instcoll']
            endpt_ctx.commit()
            for index,(block,loc) in enumerate(instances):
                node = graph.get_node(blk,loc)
                # no namespace or fragment id
                endpt_ctx.add(DFSUseNode(node,
                                         None, None,
                                         Config()))

            endpt_ctx.commit()
            for alln_ctx in \
                tac_iterate_over_sources(graph,
                                         namespace,
                                         endpt_ctx,
                                         instances,
                                         cutoff):
                routes = data['routesets']
                for route in routes:
                    last_block,last_loc,last_port = \
                            srcnode.block_name, srcnode.loc, srcport
                    route_ctx = alln_ctx.copy()
                    for block,loc,port in route[1:]:
                        if not (block == last_block and loc == last_loc):
                            curr_node = graph.get_node(block,loc)
                            last_node = graph.get_node(last_block,last_loc)
                            route_ctx.add(
                                DFSConnNode(last_node,last_port,
                                            curr_node,port))

                        last_block,last_loc,last_port = \
                                                        block,loc,port

                    print("<< route >>")
                    print(route)
                    print("<< context>>")
                    print(route_ctx)
                    route_ctx.commit()
                    route_ctx.context()
                    yield route_ctx
                    count += 1


    if count == 0:
        print("---- unusable routes ----")
        for route in unusable_routes:
            print(route)
        print("----       ***      ----")
        logger.warning("src: %s" % (srcfrag))
        logger.warning("dest: %s" % dstfrag)
        logger.warning("no connections")
        input("<press enter to continue>")


    #for curr_ctx in traverse_abs_circuit(graph,
    #                                     namespace,
    #                                     parents[0],
    #                                     ctx=ctx):
    #    srcfrag,srcport = fragment.source
    #    destfrag,destport = fragment.dest
    #    for new_ctx in \
    #        connect_conc_circ_ports(graph,curr_ctx,
    #                                namespace,
    #                                srcfrag,srcport,
    #                                destfrag,destport):
    #        yield new_ctx


def tac_abs_input(graph,namespace,fragment,ctx,cutoff):
    assert(not fragment.source is None)
    new_frag,output = fragment.source
    new_namespace = fragment.label
    for new_ctx in traverse_abs_circuit(graph,
                                        new_namespace,
                                        new_frag,
                                        ctx=ctx,cutoff=cutoff):
        source_node = new_ctx.context() \
                                .get_node_by_fragment(
                                    new_namespace,new_frag)

        new_ctx.add(DFSUseNode(source_node,
                                namespace,
                                fragment))
        new_ctx.commit()
        yield new_ctx




def traverse_abs_circuit(graph,namespace,fragment,ctx=None,cutoff=1):
    if isinstance(fragment,acirc.ABlockInst):
        for ctx in tac_abs_block_inst(graph,namespace,fragment,ctx,cutoff):
            yield ctx

    elif isinstance(fragment,acirc.AConn):
        for ctx in tac_abs_conn(graph,namespace,fragment,ctx,cutoff):
            yield ctx

    elif isinstance(fragment,acirc.AInput):
        for ctx in tac_abs_input(graph,namespace,fragment,ctx,cutoff):
            yield ctx

    elif isinstance(fragment,acirc.AJoin):
        raise Exception("unimpl: join")

    else:
        raise Exception(fragment)


def build_concrete_circuit(name,graph,fragment_map):
    namespace = list(fragment_map.keys())[0]
    fragment = fragment_map[namespace]
    for var,frag in fragment_map.items():
        logger.info("=== %s ===" % var)
        logger.info(frag)

    for idx,result in \
        enumerate(traverse_abs_circuit(graph,namespace,fragment,
                             ctx=RouteDFSState(fragment_map),
                             cutoff=3)):
        state = result.context()
        circ = ccirc.ConcCirc(graph.board,"%s_%d" % (name,idx))
        for node in state.nodes():
            circ.use(node.block_name,node.loc,config=node.config)

        for n1,p1,n2,p2 in state.conns():
            circ.conn(n1.block_name,n1.loc,p1,
                      n2.block_name,n2.loc,p2)

        yield circ

    return


def route(basename,board,node_map):
    #sys.setrecursionlimit(1000)
    graph = build_instance_graph(board)
    logger.info('--- concrete circuit ---')
    for conc_circ in build_concrete_circuit(basename,graph,node_map):
        yield conc_circ
