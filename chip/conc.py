from chip.config import Config, Labels
import json
import os

class ConcCirc:

    def __init__(self,board):
        self._board = board
        self._tau = 1.0
        self._configs= {}
        self._conns = {}
        #self._intervals = {}
        #self._bandwidths = {}

    def set_tau(self,value):
        self._tau = value

    @property
    def tau(self):
        return self._tau

    @property
    def board(self):
        return self._board

    def instances_of_block(self,block_name):
        if not block_name in self._configs:
            return

        for loc,config in self._configs[block_name].items():
            yield loc,config

    def instances(self):
        for block_name in self._configs:
            for loc,config in self._configs[block_name].items():
                yield block_name,loc,config


    def use(self,block,loc,config=None):
        if not self._board.is_block_at(block,loc):
            for block in self._board.blocks_at(loc):
                print(block.name)
            raise Exception("no block <%s> at that location.")

        if not block in self._configs:
            self._configs[block] = {}

        assert(isinstance(loc,str))
        if loc in self._configs[block]:
            if not (config is None):
                raise Exception("location with config already in system: <%s:%s>" % \
                                (block,loc))
            return

        config = Config() if config is None else config
        self._configs[block][loc] = config
        addr = (block,loc)

    def in_use(self,block_name,loc):
        if not block_name in self._configs:
            return False

        if not loc in self._configs[block_name]:
            return False

        return True

    def get_conns_by_dest(self,tblk,tloc,tport):
        for (sblock,sloc,sport), \
            (dblock,dloc,dport) in self._conns.items():
            if tblk != dblock or tloc != dloc or tport != dport:
                continue

            yield sblock,sloc,sport



    def conns_by_dest(self):
        srcs = {}
        for (sblock,sloc,sport), \
            (dblock,dloc,dport) in self._conns.items():
            if not (dblock,dloc,dport) in srcs:
                srcs[(dblock,dloc,dport)] = []

            srcs[(dblock,dloc,dport)].append((sblock,sloc,sport))


        for (dblock,dloc,dport),src_list in srcs.items():
            yield dblock,dloc,dport,src_list

    def conns(self):
        for (sblock,sloc,sport), \
            (dblock,dloc,dport) in self._conns.items():
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
            raise Exception("block <%s.%s> not in use" % (block1,loc1))

        if not self.in_use(block2,loc2):
            raise Exception("block <%s.%s> not in use" % (block1,loc1))


        if not self._board.can_connect(block1,loc1,port1,
                                       block2,loc2,port2):
            raise Exception("cannot connect <%s.%s.%s> to <%s.%s.%s>" % \
                            (block1,loc1,port1,block2,loc2,port2))


        assert(not (block1,loc1,port1) in self._conns)

        self._conns[(block1,loc1,port1)] = (block2,loc2,port2)


    def config(self,block,loc):
        return self._configs[block][loc]

    def check(self):
        return self

    @staticmethod
    def from_json(board,obj):
        circ = ConcCirc(board)
        circ.set_tau(obj['tau'])
        for inst in obj['insts']:
            assert(inst['board'] == board.name)
            config = Config.from_json(inst['config'])
            block,loc = inst['block'],inst['loc']
            circ.use(block,loc,config)

        for conn in obj['conns']:
            dest_obj = conn['dest']
            src_obj = conn['source']

            dblk = dest_obj['block']
            dport = dest_obj['port']
            dloc = dest_obj['loc']

            sblk = src_obj['block']
            sport = src_obj['port']
            sloc = src_obj['loc']

            circ.conn(sblk,sloc,sport, \
                      dblk,dloc,dport)

        return circ


    def to_json(self):
        data_struct = {
            'tau': self._tau,
            'insts': [],
            'conns':[],
            'intervals':{},
            'bandwidths':{}
        }

        for block,locs in self._configs.items():
            for loc,cfg in locs.items():
                inst = {'block':block,'loc':loc, \
                        'board':self._board.name}
                inst['config'] = cfg.to_json()
                data_struct['insts'].append(inst)

        for (src_block,src_loc,src_port), \
            (dst_block,dst_loc,dst_port) in self._conns.items():
            conn = {
                'source':{'block':src_block,'loc':src_loc,'port':src_port},
                'dest':{'block':dst_block,'loc':dst_loc,'port':dst_port}
            }
            data_struct['conns'].append(conn)

        return data_struct

    def write_circuit(self,filename):
        data = self.to_json()
        with open(filename,'w') as fh:
            strdata = json.dumps(data,indent=4)
            fh.write(strdata)


    def _build_dot_data_structures(self):
        from_id = {}
        to_id = {}
        conns = []
        index = 0
        for block_name,locs in self._configs.items():
            for loc,config in locs.items():
                block_index = index;
                blk = self._board.block(block_name)
                to_id[block_index] = {
                    'block_name':block_name,
                    'block_loc':loc,
                    'block_config':config,
                    'inputs': blk.inputs,
                    'outputs': blk.outputs
                }
                index += 1;
                for idx,inp in enumerate(blk.inputs):
                    from_id[(block_name,loc,inp)] = (block_index,"i%d" % idx)

                for idx,out in enumerate(blk.outputs):
                    from_id[(block_name,loc,out)] = (block_index,"o%d" % idx)


        for (sb,sl,sp),(db,dl,dp) in self._conns.items():
            idx1 = from_id[(sb,sl,sp)]
            idx2 = from_id[(db,dl,dp)]
            conns.append((idx1,idx2))

        return to_id,from_id,conns

    def write_graph(self,filename,write_png=False):
        undef_to_one = lambda v: 1.0 if v is None else v
        to_id,from_id,conns = self._build_dot_data_structures()
        stmts = []
        varfn = lambda idx : "N%d" % idx
        value_idx = 0;
        label_idx = 0;
        labelfn = lambda : "L%d" % label_idx
        valuefn = lambda : "V%d" % value_idx

        def q(stmt):
            stmts.append(stmt)

        #q('graph [splines=ortho, nodesep=1]')
        q('node [shape=record];')
        for idx,blkdata in to_id.items():
            inp_label = "|".join(map(
                lambda args: "<i%d> %s" % (args[0],args[1]),
                enumerate(blkdata['inputs'])))
            out_label = "|".join(map(
                lambda args: "<o%d> %s" % (args[0],args[1]),
                enumerate(blkdata['outputs'])))
            blk_name = blkdata['block_name']
            blk_loc = blkdata['block_loc']
            blk_label = "%s|%s" % (blk_name,blk_loc)
            cfg = blkdata['block_config']
            mode_label = "cm-m:%s|sc-m:%s" % (cfg.comp_mode, cfg.scale_mode)
            label = "{{%s}|{%s}|{%s}|{%s}}}" %  \
                    (inp_label,blk_label,mode_label,out_label)
            st = "%s [label=\"%s\"]" % (varfn(idx),label)
            q(st)

            for port,math_label,kind in cfg.labels():
                kind = kind.value
                scf = undef_to_one(cfg.scf(port))
                label = "%s %s*%.3f t:%.3f" % (kind,math_label,scf,self.tau)
                st = "%s [label=\"%s\"]" % (labelfn(),label)
                _,portidx = from_id[(blk_name,blk_loc,port)]
                q(st)
                st = "%s:%s -> %s" % (varfn(idx),portidx,labelfn())
                q(st)
                label_idx += 1

            for port,value in cfg.values():
                scf = undef_to_one(cfg.scf(port))
                label = "%.3f*%.3f" % (value,scf)
                st = "%s [label=\"%s\"]" % (valuefn(),label)
                q(st)
                _,portidx = from_id[(blk_name,blk_loc,port)]
                st = "%s -> %s:%s" % (valuefn(),varfn(idx),portidx)
                q(st)
                value_idx += 1

                vnode = valuefn()

        for (src,h1),(dst,h2) in conns:
            q("%s:%s -> %s:%s" % (varfn(src),h1,varfn(dst),h2))

        prog = "digraph circuit {\n%s\n}" % ("\n".join(stmts))
        with open(filename,'w') as fh:
            fh.write(prog)

        if write_png:
            assert(".dot" in filename)
            basename = filename.split(".dot")[0]
            imgname = "%s.png" % basename
            cmd = "dot -Tpng %s -o %s" % (filename,imgname)
            os.system(cmd)
