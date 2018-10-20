import chip.block as block



class ANode:

    class CopyCtx:

        def __init__(self):
            self._map = {}

        def get(self,node):
            return self._map[hash(node)]

        def register(self,node,new_node):
            assert(not new_node is None)
            if hash(node) in self._map:
                return False

            new_node._id = node._id
            self._map[hash(node)] = new_node
            return True

        def copy(self,node):
            if hash(node) in self._map:
                return self._map[hash(node)]

            else:
                new_node = node._copy(self)
                if not self.register(node,new_node):
                    return self.get(node)

            nn = self._map[hash(node)]
            assert(not nn is None)
            assert(str(nn) == str(node))
            return nn

    def __init__(self):
        self._children = []
        self._parents = []
        self._node_cache = set([self])
        self._id = None

    @property
    def id(self):
        return self._id

    def contains(self,n):
        return n in self.nodes()

    def nodes(self):
        def helper(curr_node):
            if len(curr_node._parents) > 0:
                for par in curr_node._parents:
                    for node in helper(par):
                        yield node

            else:
                for node in curr_node._node_cache:
                    yield node

        return set(helper(self))

    def enumerate(self):
        for idx,node in enumerate(self.nodes()):
            node._id = idx

    def get_by_id(self,ident):
        for node in self.nodes():
            assert(not node.id is None)
            if ident == node.id:
                return node

        raise Exception("no node with that id")

    def _add_nodes_to_cache(self,ns):
        upd = []
        for n in ns:
            if not n in self._node_cache:
                self._node_cache.add(n)
                upd.append(n)

        for par in self._parents:
            par._add_nodes_to_cache(upd)

    def add_child(self,node):
        assert(not node in self._children)
        node._parents.append(self)
        self._children.append(node)
        self._add_nodes_to_cache([node])

    def add_parent(self,node):
        assert(not node in self._parents)
        self._parents.append(node)
        node._children.append(node)
        node._add_nodes_to_cache(self._node_cache)

    def parents(self):
        for par in self._parents:
            yield par

    def children(self):
        for ch in self._children:
            yield ch

    def filter_ancestors(self,fn):
        if fn(self):
            yield self

        for child in self._children:
            for result in child.children(fn):
                yield result

    @staticmethod
    def make_node(board,name):
        block = board.block(name)
        node = ABlockInst(block)
        return node

    @staticmethod
    def connect(node1,output,node2,inp):
        assert(not node1 is None)
        assert(not node2 is None)
        conn = AConn(node1,output,node2,inp)

    def copy(self):
        engine = ANode.CopyCtx()
        return self._copy(engine),engine

class AInput(ANode):

    def __init__(self,name):
        ANode.__init__(self)
        self._name = name
        self._source = None

    def set_source(self,node,output):
        self._source = (node,output)

    @property
    def label(self):
        return self._name

    @property
    def source(self):
        return self._source

    @property
    def name(self):
        if self._id is None:
            return "%s" % self._name
        else:
            return "%d.%s" % (self._id,self._name)

    def _copy(self,engine):
        node = AInput(self._name)
        success = engine.register(self,node)
        if not success:
            return eng.get(self)

        if not self._source is None:
            old_node,output = self._source
            new_node = engine.copy(old_node)
            node._source = (new_node,output)

        return node

    def __repr__(self):
        if self._source is None:
            return "@%s <= NULL" % self._name
        else:
            return "@%s <= %s.%s" % (self._name,
                                     self._source[0].name,
                                     self._source[1])

class AJoin(ANode):

    def __init__(self):
        ANode.__init__(self)

    @property
    def name(self):
        if self._id is None:
            return "+"
        else:
            return "%d.+" % (self._id)

    def _copy(self,eng):
        join = AJoin()
        success = eng.register(self,join)
        if not success:
            return eng.get(self)

        for node in self.parents():
            eng.copy(node)

        for node in self.children():
            eng.copy(node)

        return join

    def make(self):
        node = AJoin()
        return node

    def __repr__(self):
        argstr = " ".join(map(lambda p: str(p),self._parents))
        return "(%s %s)" % (self.name,argstr)

class AConn(ANode):

    def __init__(self,node1,port1,node2,port2):
        ANode.__init__(self)
        self._src_port = port1
        self._dst_port = port2
        self._src_node = None
        self._dst_node = None
        if not node1 is None and not node2 is None:
            self._set_nodes(node1,node2)

    def _set_nodes(self,src_node,dst_node):
        assert(self._src_node is None)
        assert(self._dst_node is None)
        assert(not src_node is None)
        assert(not dst_node is None)
        self._src_node = src_node
        self._dst_node = dst_node
        if isinstance(self._src_node,ABlockInst):
            assert(self._src_port in self._src_node.block.outputs)

        self._src_node.add_child(self)

        if isinstance(self._dst_node,ABlockInst):
            assert(self._dst_port in self._dst_node.block.inputs)

        self.add_child(self._dst_node)

        
    def _copy(self,eng):
        conn = AConn(None,self._src_port,None,self._dst_port)
        success = eng.register(self,conn)
        if not success:
            eng.get(self)

        src_n = eng.copy(self._src_node)
        dst_n = eng.copy(self._dst_node)
        conn._set_nodes(src_n,dst_n)
        return conn


    @property
    def source(self):
        return self._src_node,self._src_port

    @property
    def dest(self):
        return self._dst_node,self._dst_port

    @property
    def name(self):
        if self._id is None:
            return "="
        else:
            return "%d.=" % (self._id)


    def __repr__(self):
        return "(%s %s %s %s)" % \
            (self.name,self._dst_port,self._src_port, self._src_node)


class ABlockInst(ANode):
    def __init__(self,node):
        ANode.__init__(self)
        self._block = node
        self._inputs = node.inputs
        self._outputs = node.outputs
        self.config = block.Config()
        self._used = []

    @property
    def block(self):
        return self._block

    def _copy(self,eng):
        blk = ABlockInst(self._block)
        success = eng.register(self,blk)
        if not success:
            return eng.get(self)

        for par in self.parents():
            eng.copy(par)

        for ch in self.children():
            eng.copy(ch)

        return blk

    @property
    def name(self):
        if self._id is None:
            return "blk %s" % (self._block.name)
        else:
            return "%d.blk %s" % (self._id,self._block.name)

    def use_output(self,output):
        assert(output in self._outputs)
        assert(not output in self._used)
        self._used.append(output)

    def output_used(self,output):
        return output in self._used

    def __repr__(self):
        argstr = " ".join(map(lambda p: str(p), self._parents))
        return "(%s %s)" % (self.name,argstr)

class AbsCirc:

    def __init__(self,board):
        self._board = board

    @property
    def board(self):
        return self._board

    @staticmethod
    def count_instances(board,root_nodes):
        counts = dict(map(lambda b: (b.name,0), board.blocks))
        for root_node in root_nodes:
            for node in filter(lambda x : isinstance(x,ABlockInst),
                root_node.nodes()):
                counts[node.block.name] += 1

        return counts

    @staticmethod
    def feasible(board,root_nodes):
        counts = dict(map(lambda b: (b.name,0), board.blocks))
        for root_node in root_nodes:
            for node in filter(lambda x : isinstance(x,ABlockInst),
                root_node.nodes()):
                counts[node.block.name] += 1
                if counts[node.block.name] > \
                   board.num_blocks(node.block.name):
                    return False


        return True
