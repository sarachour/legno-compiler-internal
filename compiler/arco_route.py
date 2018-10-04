from chip.block import Block
import chip.abs as acirc
import sys

class RouteGraph:
    class RNode:

        def __init__(self,graph,block,loc):
            self._graph = graph
            self._loc = loc
            self._block = block
            self._inputs = graph.board.block(block).inputs
            self._outputs = graph.board.block(block).outputs
            self._passthrough = (graph.board.block(block).type == Block.BUS)

        @property
        def loc(self):
            return self._loc

        @property
        def block_name(self):
            return self._block

        @property
        def key(self):
            return "%s%s" % (self._block,str(self._loc))

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
        self._out_to_in = {}
        self._in_to_out = {}
        self.board = board


    def add_node(self,block_name,loc):
        node = RouteGraph.RNode(self,block_name,loc)
        if not block_name in self._nodes_by_block:
            self._nodes_by_block[block_name] = []

        self._nodes_by_block[block_name].append(node.key)
        self._nodes[node.key] = node
        for okey in node.output_keys():
            self._out_to_in[okey] = {}

        for ikey in node.input_keys():
            self._in_to_out[ikey] = {}

    def get_node(self,block_name,loc):
        node = RouteGraph.Node(self,block_name,loc)
        return self._nodes[node.key]

    def nodes_of_block(self,block_name,used=[]):
        for node_key in self._nodes_by_block[block_name]:
            node = self._nodes[node_key]
            if not node.key in used:
                yield node




GRAPHS = {}
def build_instance_graph(board):
    if board.name in GRAPHS:
        return GRAPHS[board.name]

    graph = RouteGraph(board)
    for block,loc,metadata in board.instances():
        graph.add_node(block,loc[1:])

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
        self._pools_by_fragment_id = {}
        self._conns = {}

    def get_pool_by_fragment_id(self,namespace,pool):
        if not (namespace,pool) in self._pools_by_fragment_id:
            return None

        return self._pools_by_fragment_id[(namespace,pool)]


    def get_node_by_fragment_id(self,namespace,frag):
        if not (namespace,frag) in self._nodes_by_fragment_id:
            return None

        return self._nodes_by_fragment_id[(namespace,frag)]

    def nodes(self,block):
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
            if board.position_string(node.loc) ==  \
               board.position_string(loc):
                return True

        return False


    def use_node(self,node,config,namespace,fragment_id):
        if (namespace,fragment_id) in self._nodes_by_fragment_id:
            raise Exception ("%s.%d already in context" % (namespace,fragment_id))

        self._nodes_by_fragment_id[(namespace,fragment_id)] = node
        if not node.block_name in self._nodes_by_block:
            self._nodes_by_block[node.block_name] = []

        self._nodes_by_block[node.block_name].append(node)

    def conn_node(self,node1,port1,node2,port2):
        assert(not node1.output_key(port1) in self._conns)
        self._conns[node1.output_key(port1)] = (node1,port1,node2,port2)

    def add_to_pool(self,node,port,pool_ns,pool_id):
        if (not (pool_ns,pool_id) in self._pools_by_fragment_id):
            self._pools_by_fragment_id[(pool_ns,pool_id)] = []

        self._pools_by_fragment_id[(pool_ns,pool_id)].append((node,port))

class DFSPoolNode(DFSAction):

    def __init__(self,node,port,namespace,frag_id):
        DFSAction.__init__(self)
        self._namespace = namespace
        self._frag_id = frag_id
        self._node = node
        self._port = port


    def apply(self,ctx):
        ctx.add_to_pool(self._node,self._port,self._namespace,self._frag_id)


class DFSUseNode(DFSAction):

    def __init__(self,node,namespace,frag_id,config=None):
        DFSAction.__init__(self)
        self._namespace = namespace
        self._frag_id = frag_id
        self._node = node
        self._config = config


    def apply(self,ctx):
        ctx.use_node(self._node,self._config,self._namespace,self._frag_id)

    def __repr__(self):
        return "%s [%s.%d]" % (self._node,self._namespace,self._frag_id)

class DFSConnNode(DFSAction):

    def __init__(self,node1,port1,node2,port2):
        self._n1 = node1
        self._n2 = node2
        self._p1 = port1
        self._p2 = port2

    def apply(self,ctx):
        ctx.conn_node(self._n1,self._p2,self._n2,self._p2)

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
        self._stack = self._stack[1:]

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
                rep += str(op) + "\t"
            rep += "\n"
        return rep



class RouteDFSState(DFSState):

    def __init__(self,fragment_map):
        DFSState.__init__(self)
        self._fragments = fragment_map

    def make_new(self):
        return RouteDFSState(self._fragments)


    def new_ctx(self):
        return RouteDFSContext()

def connect_conc_circ_ports(graph,state,namespace,src_frag,src_port,dest_frag,dest_port):
    cctx = state.context()
    if isinstance(src_frag,acirc.AInput):
        srcnode = cctx.get_node_by_fragment_id(namespace,src_frag.id)
        src_port = src_frag.source[1]
    elif isinstance(src_frag,acirc.AJoin):
        srcpool = cctx.get_pool_by_fragment_id(namespace,src_frag.id)
        for node,port in srcpool:
            raise Exception("build context")

    else:
        srcnode = cctx.get_node_by_fragment_id(namespace,src_frag.id)

    if isinstance(dest_frag,acirc.AJoin):
        state.commit()
        state.add(DFSPoolNode(srcnode,src_port,namespace,dest_frag.id))
        state.commit()
        return state
        return
    else:
        dstnode = cctx.get_node_by_fragment_id(namespace,dest_frag.id)

    assert(not dstnode is None)
    assert(not srcnode is None)
    if graph.can_connect(srcnode.block_name,srcnode.loc,src_port,
                         dstnode.block_name,dstnode.loc,dest_port):
        state.add(DFSConnNode(srcnode,src_port,dstnode,dest_port))
        state.commit()
        return state

    else:
        # TODO: allow for gaps
        print("cannot connec %s%s.%s - %s%s.%s" %
            (srcnode.block_name,srcnode.loc,src_port,dstnode.block_name,dstnode.loc,dest_port))
        return


def are_block_instances_used(graph,ctx,lst):
    for block,loc in lst:
        if ctx.in_use(graph.board,block,loc):
            return True

    return False

def tac_abs_block_inst(graph,namespace,fragment,ctx=None,cutoff=1,loc=None):
    node = ctx.context().get_node_by_fragment_id(
        namespace,fragment.id)
    if not node is None:
        yield ctx
        return

    used_nodes = ctx.context().nodes(fragment.block.name)
    ctx.commit()
    for node in graph.nodes_of_block(fragment.block.name,
                                        used=used_nodes):
        if not loc is None and \
           graph.board.position_string(node.loc) != graph.board.position_string(loc):
            continue

        ctx_buf=[ctx.copy()]
        ctx_buf[0].add(DFSUseNode(node,namespace,
                                    fragment.id,
                                    fragment.config))
        ctx_buf[0].commit()
        for source_frag in fragment.parents():
            new_ctx_buf = []
            for curr_ctx in ctx_buf:
                for new_ctx in \
                    traverse_abs_circuit(graph,
                                            namespace,
                                            source_frag,
                                            ctx=curr_ctx,
                                            cutoff=cutoff
                ):
                    new_ctx_buf.append(new_ctx.copy())

            ctx_buf = new_ctx_buf

        for new_ctx in ctx_buf:
            yield new_ctx

        ctx.pop()

def tac_abs_conn(graph,namespace,fragment,ctx,cutoff):
    parents = list(fragment.parents())
    assert(len(parents) == 1)
    # find other edge
    srcfrag,srcport = fragment.source
    dstfrag,dstport = fragment.dest
    dstnode = ctx.context().get_node_by_fragment_id(namespace,dstfrag.id)
    if isinstance(srcfrag,acirc.AInput):
        srcfrag,srcport = srcfrag.source

    if isinstance(srcfrag,acirc.ABlockInst):
        curr_state = ctx.context()
        count = 0
        for srcloc in graph.board.instances_of_block(srcfrag.block.name):
            if are_block_instances_used(graph,curr_state,
                                        [(srcfrag.block.name,srcloc)]):
                continue

            for route in \
                graph.board.find_routes(srcfrag.block.name,srcloc,srcport,
                                        dstnode.block_name,dstnode.loc,dstport,
                                        cutoff=cutoff):
                if are_block_instances_used(graph, curr_state,
                                            map(lambda args:(args[0],args[1]),
                                                route[:-1])):
                    continue

                new_ctx = ctx.copy()
                for idx,hop in enumerate(route):
                    if idx >= len(route) - 2 or idx % 2 == 0:
                        continue

                    chop_blk,chop_loc,chop_port = hop
                    nhop_blk,nhop_loc,nhop_port = route[idx+1]

                    cnode = graph.get_node(chop_blk,chop_loc)
                    nnode = graph.get_node(nhop_blk,nhop_loc)

                    new_state = new_ctx.context()
                    if not new_ctx.in_use(chop_blk,chop_loc):
                        new_ctx.add(DFSUseNode(cnode,None, None, Config()))

                    if not new_ctx.in_use(nhop_blk,nhop_loc):
                        new_ctx.add(DFSUseNode(nnode,None, None, Config()))

                    state.add(DFSConnNode(cnode,chop_port,nnode,nhop_port))
                    new_ctx.commit()

                print(route)
                # actually traverse source
                for newest_ctx in tac_abs_block_inst(graph,
                                                     namespace,
                                                     srcfrag,
                                                     ctx=new_ctx,
                                                     loc=srcloc):
                    last_hop_blk,last_hop_loc,last_hop_port = route[-2]
                    cnode = graph.get_node(last_hop_blk,last_hop_loc)
                    nnode = graph.get_node(srcfrag.block.name,srcloc)

                    newest_ctx.add(DFSConnNode(cnode,last_hop_port,
                                               srcnode,srcport))
                    newest_ctx.commit()
                    count += 1
                    yield newest_ctx


        if count == 0:
            print("src: %s\n" % (srcfrag))
            print("dest: %s\n" % dstfrag)
            raise Exception("no connections")

    else:
        raise Exception("unsupported source <%s>" % srcfrag.__class__.__name__)

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
                                .get_node_by_fragment_id(
                                    new_namespace,new_frag.id)

        new_ctx.add(DFSUseNode(source_node,
                                namespace,
                                fragment.id))
        new_ctx.commit()
        yield new_ctx


def tac_abs_join(graph,namespace,fragment,ctx,cutoff):
    ctx_buf = [ctx.copy()]
    for join_frag in fragment.parents():
            new_ctx_buf = []
            for curr_ctx in ctx_buf:
                for new_ctx in traverse_abs_circuit(graph,namespace,\
                                                    join_frag,
                                                    ctx=curr_ctx,
                                                    cutoff=cutoff):
                    new_ctx_buf.append(new_ctx.copy())

            ctx_buf = new_ctx_buf

    for new_ctx in ctx_buf:
        raise Exception("create join operation")


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
        tac_abs_join(graph,namespace,fragment,ctx,cutoff)

    else:
        raise Exception(fragment)


def build_concrete_circuit(graph,fragment_map):
    namespace = fragment_map.keys()[0]
    fragment = fragment_map[namespace]
    for var,frag in fragment_map.items():
        print("=== %s ===" % var)
        print(frag)

    for _ in range(0,5):
        print("######")
    for result in \
        traverse_abs_circuit(graph,namespace,fragment,
                             ctx=RouteDFSState(fragment_map),
                             cutoff=3):
        return result

    return None


def route(board,_fragment_map):
    fragment_map = dict(map(lambda args: (args[0],args[1][0]), _fragment_map.items()))
    for frag in fragment_map.values():
        frag.enumerate()
    sys.setrecursionlimit(100000)
    graph = build_instance_graph(board)
    return build_concrete_circuit(graph,fragment_map)
    raise NotImplementedError
