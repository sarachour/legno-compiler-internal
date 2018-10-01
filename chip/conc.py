from chip.block import Config, Labels

class ConcCirc:

    def __init__(self,board,name):
        self._board = board
        self.name = name
        self._tau = 1.0
        self._blocks = {}
        self._conns = {}
        self._intervals = {}

    def set_tau(self,value):
        self._tau = value

    @property
    def tau(self):
        return self._tau

    def set_interval(self,label,lb,ub):
        self._intervals[label] = (lb,ub)

    def interval(self,label):
        if not (label in self._intervals):
            raise Exception("unknown interval: %s" % label)
        return self._intervals[label]

    @property
    def board(self):
        return self._board

    def instances(self):
        for block_name in self._blocks:
            for loc,config in self._blocks[block_name].values():
                yield block_name,loc,config


    def use(self,block,loc):
        if not self._board.is_block_at(block,loc):
            for block in self._board.blocks_at(loc):
                print(block.name)
            raise Exception("no block <%s> at that location.")

        if not block in self._blocks:
            self._blocks[block] = {}

        locstr = self.board.position_string(loc)
        if locstr in self._blocks[block]:
            return

        self._blocks[block][locstr] = (loc,Config())
        addr = (block,loc)

    def in_use(self,block_name,loc):
        if not block_name in self._blocks:
            return False

        addrstr = self.board.position_string(loc)
        if not addrstr in self._blocks[block_name]:
            return False

        return True

    def conns_by_dest(self):
        for dests in self._conns.values():
            srcs = []
            for saddr,sport,daddr,dport in dests.values():
                sloc = self.board.position_string_to_position(saddr)
                srcs.append((sloc,sport))

            yield daddr,dport,srcs

    def conns(self):
        for dests in self._conns.values():
            for sblock,sloc,sport,dblock,dloc,dport in dests.values():
                yield sblock,sloc,sport,dblock,dloc,dport

    def has_conn(self,block1,loc1,port1,block2,loc2,port2):
        return self._board.can_connect(block1,loc1,port1,
                                       block1,loc2,port2)


    def find_routes(self,block1,loc1,port1,block2,loc2,port2):
        for path in self._board.find_routes(block1,loc1,port1,
                                            block2,loc2,port2):
            yield path


    def conn(self,block1,loc1,port1,block2,loc2,port2):
        if not self.in_use(block1,loc1):
            raise Exception("block <%s> not in use" % (addr1str))

        if not self.in_use(block2,loc2):
            raise Exception("block <%s> not in use" % (addr2str))


        if not self._board.can_connect(block1,loc1,port1,
                                       block2,loc2,port2):
            raise Exception("cannot connect <%s.%s> to <%s.%s>" % \
                            (addr1,port1,addr2,port2))


        addr1 = self.board.position_string(loc1)
        addr2 = self.board.position_string(loc2)
        if not (block2,addr2,port2) in self._conns:
            self._conns[(block2,addr2,port2)] = {}

        self._conns[(block2,addr2,port2)][(block1,addr1,port1)] \
            = (block1,loc1,port1,block2,loc2,port2)


    def config(self,block,loc):
        addr = self.board.position_string(loc)
        return self._blocks[block][addr][1]

    def check(self):
        return self
