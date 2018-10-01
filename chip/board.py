import networkx as nx
from chip.block import Block

class Layer:

    def __init__(self,board,index,parent=None):
        self._index = index
        self._board = board
        self._parent = parent
        self._layers = {}

    def sublayer(self,pos):
        layer = self.layer(pos[0])
        if len(pos) > 1:
            return layer.sublayer(pos[1:])
        else:
            return layer

    def layer(self,index):
        if (index in self._layers):
            return self._layers[index]

        layer = Layer(self._board,index,parent=self)
        self._layers[index] = layer
        return layer

    @staticmethod
    def position_string(position):
        return "(%s)" % \
            (",".join(map(lambda idx: str(idx), position)))

    @property
    def position(self):
        pos = [] if self._parent is None else self._parent.position
        pos.append(self._index)
        return pos

    def make_position(self,subpos):
        localpos = [self._index] + subpos if not self._parent is None \
                   else subpos

        return localpos if self._parent is None else \
            self._parent.make_position(localpos)


    @property
    def index(self):
        return self._index


    def subpositions(self,recurse=False):
        if len(self._layers) == 0:
            yield [] if not recurse else [self._index]

        for layer in self._layers.values():
            for subp in layer.subpositions(recurse=True):
                yield subp

    def inst(self,block_name):
        self._board.inst(block_name,self.position)
        pass

class Board(Layer):

    CURRENT_MODE = 0
    VOLTAGE_MODE = 1
    MIXED_MODE = 2

    def __init__(self,name,mode):
        Layer.__init__(self,self,name)
        self._name = name
        self._mode = mode
        self._blocks = {}
        self._inst_by_block = {}
        self._inst_by_position = {}
        self._connections = {}
        self._routes = nx.DiGraph()
        self._metadata = {}
        self._freeze_insts = False

    def freeze_instances(self):
        self._freeze_insts =  True

    @property
    def name(self):
        return self._name

    @property
    def blocks(self):
        for block in self._blocks.values():
            yield block

    def block(self,name):
        return self._blocks[name]

    def has_block(self,name):
        return name in self._blocks

    def num_blocks(self,name):
        return len(self._inst_by_block[name])

    def instances(self):
        for blk,locs in self._inst_by_block.items():
            for loc,meta in locs.values():
                yield blk,loc,meta

    def instances_of_block(self,blk):
        if not blk in self._inst_by_block:
            for oblk in self._inst_by_block.keys():
                print(oblk)
            raise Exception("no instances <%s>" % blk)

        for loc in self._inst_by_block[blk]:
            yield self._inst_by_position[loc]['pos']

    @property
    def mode(self):
        return self._mode

    def set_meta(self,key,value):
        self._metadata[key] = value

    def meta(self,key):
        return self._metadata[key]

    def set_inst_meta(self,block_name,pos,key,value):
        posstr = Layer.position_string(pos)
        _,meta = self._inst_by_block[block_name][posstr]
        assert(not key in meta)
        meta[key] = value

    def inst_meta(self,block_name,pos,key):
        posstr = self.position_string(pos)

        if not posstr in self._inst_by_block[block_name]:
            for key in self._inst_by_block[block_name].keys():
                print(key)

            raise Exception("position <%s> not available for block <%s>" % (posstr,block_name))
        _,meta = self._inst_by_block[block_name][posstr]
        if not (key in meta):
            for in_key in meta:
                print(in_key)
            raise Exception("<%s> not in metadata for %s.%s" % \
                            (key,block_name,posstr))

        return meta[key]

    def add(self,block_specs):
        for blk in block_specs:
            assert(not blk.name in self._blocks)
            self._blocks[blk.name] = blk

    def block_locs(self,scope,block):
        def is_prefixed(super_l,sub_l):
            assert(len(super_l) <= len(sub_l))
            for idx in range(0,len(super_l)):
                if super_l[idx] != sub_l[idx]:
                    return False

            return True

        if block in self._inst_by_block:
            for loc,_ in self._inst_by_block[block].values():
                if is_prefixed(scope.position,loc):
                    yield loc[1:]

        else:
            return


    def is_block_at(self,block,position):
        if position[0] == self._name:
            posstr = Layer.position_string(position)
        else:
            posstr = Layer.position_string([self._name] + position)
        if not posstr in self._inst_by_position:
            raise Exception("unknown position: %s" % posstr)

        elif block in self._inst_by_position[posstr]['blocks']:
            return True

        else:
            return False


    def position_string(self,position):
        if position[0] == self._name:
            posstr = Layer.position_string(position)
        else:
            posstr = Layer.position_string([self._name]+position)

        return posstr

    def find_routes(self,sblk,sloc,sport,dblk,dloc,dport,cutoff=3):
        skey = self.position_string(sloc)
        dkey = self.position_string(dloc)

        if self.can_connect(sblk,sloc,sport,dblk,dloc,dport):
            print("CAN CONNECT")
            yield [(sblk,skey,sport),(dblk,dkey,dport)]


        for route in nx.all_simple_paths(self._routes,
                                         source=(sblk,skey,sport),
                                         target=(dblk,dkey,dport),
                                         cutoff=cutoff):
            yield list(map(lambda (b,a,p):
                           (b,self._inst_by_position[a]['pos'],p),
                           route))

    def inst(self,block_name,position):
        assert(not self._freeze_insts)
        if not block_name in self._inst_by_block:
            self._inst_by_block[block_name] = {}

        key = self.position_string(position)
        if not key in self._inst_by_position:
            self._inst_by_position[key] = {'pos':position,'blocks':[]}

        if(key in self._inst_by_block[block_name]):
            raise Exception("block <%s> already in position <%s>" % \
                            (block_name,key))
        assert(not block_name in self._inst_by_position[key]['blocks'])

        self._inst_by_block[block_name][key] = (position,{})
        self._inst_by_position[key]['blocks'].append(block_name)
        block = self.block(block_name)
        if block.type == Block.BUS:
            assert(len(block.inputs) == 1)
            assert(len(block.outputs) == 1)

            self._routes.add_node((block_name,key,block.inputs[0]))
            self._routes.add_node((block_name,key,block.outputs[0]))
            self._routes.add_edge((block_name,key,block.inputs[0]),
                                  (block_name,key,block.outputs[0]))

    def blocks_at(self,position):
        key = Layer.position_string([self._name] + position)
        for block_name in self._inst_by_position[key]['blocks']:
            yield self._blocks[block_name]

    def can_connect(self,sblk,spos,sport,dblk,dpos,dport):
        skey = self.position_string(spos)
        dkey = self.position_string(dpos)

        sblkport = (sblk,sport)
        dblkport = (dblk,dport)
        if not sblkport in self._connections:
            return False

        if not dblkport in self._connections[sblkport]:
            print(self._connections[sblkport].keys())
            return False

        if not (skey,dkey) in self._connections[sblkport][dblkport]:
            return False

        return True


    def inverts_signal(self,sblk,spos,sport,dblk,dpos,dport):
        skey = self.position_string(spos)
        dkey = self.position_string(dpos)
        _,_,invert = self._connections[(sblk,sport)][(dblk,dport)][(skey,dkey)]
        return invert

    def connections(self):
        for (sblk,sport) in self._connections:
            for (dblk,dport) in self._connections[(sblk,sport)]:
                for spos,dpos in self._connections[(sblk,sport)][(dblk,dport)].values():
                    yield (sblk,spos,sport),(dblk,dpos,dport)

    def conn(self,sblkname,spos,sport,dblkname,dpos,dport):
        assert(self._freeze_insts)
        skey = self.position_string(spos)
        dkey = self.position_string(dpos)
        if not skey in self._inst_by_block[sblkname]:
            print(self._inst_by_block[sblkname].keys())
            raise Exception("<%s> not in list of defined instances for <%s>"
                            % (skey,sblkname))
        if not dkey in self._inst_by_block[dblkname]:
            print(self._inst_by_block[dblkname].keys())
            raise Exception("<%s> not in list of defined instances for <%s>"
                            % (skey,dblkname))

        if not sblkname in self._blocks:
            print(self._blocks.keys())
            raise Exception("<%s> not in block list" % sblkname)

        if not dblkname in self._blocks:
            print(self._blocks.keys())
            raise Exception("<%s> not in block list" % dblkname)

        sblk = self._blocks[sblkname]
        dblk = self._blocks[dblkname]
        assert(sblk.is_output(sport))
        assert(dblk.is_input(dport))
        sblkport = (sblkname,sport)
        dblkport = (dblkname,dport)

        if not sblkport in self._connections:
            self._connections[sblkport] = {}

        if not dblkport in self._connections[sblkport]:
            self._connections[sblkport][dblkport] = {}

        self._connections[sblkport][dblkport][(skey,dkey)] = (spos,dpos)

        if self._routes.has_node((sblkname,skey,sport)) and \
           not self._routes.has_node((dblkname,dkey,dport)):
            self._routes.add_node((dblkname,dkey,dport))
            self._routes.add_edge((sblkname,skey,sport),
                                  (dblkname,dkey,dport))

        if not self._routes.has_node((sblkname,skey,sport)) and \
           self._routes.has_node((dblkname,dkey,dport)):
            self._routes.add_node((sblkname,skey,sport))


        if self._routes.has_node((sblkname,skey,sport)) and \
           self._routes.has_node((dblkname,dkey,dport)):
            self._routes.add_edge((sblkname,skey,sport),
                                  (dblkname,dkey,dport))
