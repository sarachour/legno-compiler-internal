import chip.conc
import lang.experiment as experiments
from chip.block import Labels
import os
import math

class Logger:
    LOCS = {}
    NATIVE = True
    DEBUG = False

    @staticmethod
    def interface():
        if Logger.NATIVE:
            return "SerialUSB"
        else:
            return "Serial"

    @staticmethod
    def debug(arr,tag,msg,println=True,literal=True,indent=""):
        if not tag in Logger.LOCS:
            Logger.LOCS[tag] = 0

        assert(literal)
        full_msg = "[%s][%d] %s" % (tag,Logger.LOCS[tag],msg)

        if not Logger.DEBUG:
            return

        Logger.LOCS[tag] += 1
        Logger.data(arr,full_msg,prefix="[D]",
                      println=println,
                      literal=literal,
                      indent=indent)

    @staticmethod
    def info(arr,msg,println=True,literal=True,indent=""):
        Logger.data(arr,msg,prefix="",
                      println=println,
                      literal=literal,
                      indent=indent)

    @staticmethod
    def data(arr,msg,prefix="",println=True,literal=True,indent=""):
        fn = "println" if println else "print"
        prefix = prefix if prefix == "" else prefix + " "
        msg = prefix + msg if not literal else msg
        smsg = "\"%s\"" % msg if literal else msg

        if Logger.NATIVE:
            msg = "%sSerialUSB.%s(%s);" % (indent,fn,smsg)
        else:
            msg = "%sSerial.%s(%s);" % (indent,fn,smsg)

        arr.append(msg)


cant_enable = ["tile_out","tile_in","chip_out","due_adc"]
block_type = {
    "integrator": "Fabric::Chip::Tile::Slice::Integrator",
    "tile_out": "Fabric::Chip::Tile::Slice::TileInOut",
    "tile_in": "Fabric::Chip::Tile::Slice::TileInOut",
    "tile_dac": "Fabric::Chip::Tile::Slice::Dac",
    "multiplier": "Fabric::Chip::Tile::Slice::Multiplier",
    "fanout": "Fabric::Chip::Tile::Slice::Fanout",
    "chip_in": "Fabric::Chip::Tile::Slice::ChipInput",
    "chip_out": "Fabric::Chip::Tile::Slice::ChipOutput",
    "due_adc": "Fabric::Chip::Tile::Slice::ChipOutput"
}
block_assign_fmt_str = {
    "integrator" : (3,"chips[%d].tiles[%d].slices[%d].integrator"),
    "tile_out" : (4,"chips[%d].tiles[%d].slices[%d].tileOuts[%d]"),
    "tile_in" : (4,"chips[%d].tiles[%d].slices[%d].tileInps[%d]"),
    "tile_dac" : (3,"chips[%d].tiles[%d].slices[%d].dac"),
    "multiplier" : (4,"chips[%d].tiles[%d].slices[%d].muls[%d]"),
    "fanout": (4,"chips[%d].tiles[%d].slices[%d].fans[%d]"),
    "chip_in": (3,"chips[%d].tiles[%d].slices[%d].chipInput"),
    "chip_out": (3,"chips[%d].tiles[%d].slices[%d].chipOutput"),
    "due_adc": (3,"chips[%d].tiles[%d].slices[%d].chipOutput")
}

block_port = {
    "integrator" : {
        "in" : "in0",
        "out" : "out0",
    },
    "fanout":  {
        "in": "in0",
        "out0" : "out0",
        "out1" : "out1",
        "out2" : "out2"
    },
    "multiplier": {
        "in0": "in0",
        "in1": "in1",
        "out":"out0"
    },
    "tile_out": {
        "in": "in0",
        "out": "out0"
    },
    "tile_in": {
        "in": "in0",
        "out": "out0"
    },
    "chip_out": {
        "in": "in0",
        "out": "out0"
    },
    "due_adc": {
        "in": "in0",
        "out": "out0"
    },
    "tile_dac": {
        "in": "in0",
        "out": "out0"
    }

}
class SymbolTable:

    abbrv = {
        "integrator" : "int",
        "tile_out": "tout",
        "tile_in":"tin",
        "multiplier": "mult",
        "fanout": "fan",
        "chip_out": "cout",
        "chip_in":"cin",
        "due_adc": "cout",
        "tile_dac": "tdac"

    }

    def __init__(self,board):
        self._fdecls = {}
        self._rdecls = {}
        self.board = board


    def get_by_loc(self,block_name,loc):
        if isinstance(loc,str):
            raise Exception("expected list <%s>" % loc)
        return self._fdecls[(block_name,self.board.position_string(loc))]

    def new_inst(self,blockname,loc):
        pos_str = "_".join(map(lambda x: str(x),loc))
        var_name = "%s_%s" % (SymbolTable.abbrv[blockname],\
                                pos_str)
        key = self.board.position_string(loc)
        self._fdecls[(blockname,key)] = var_name
        self._rdecls[var_name] = loc
        return var_name

#HCDC_DEMO_BOARD
def chip_version():
    return 4


def get_DUE_scale_and_offset():
    # PASTE SCALE AND OFFSET HERE
    SCALE=-0.00208512661642
    OFFSET=4.2912124704

    return SCALE,OFFSET

def make_decl(sym_tbl,fab_name,block_name,loc):
    if not block_name in block_type:
        raise Exception("unsupported: %s" % block_name)

    var_type = block_type[block_name]
    n_pos_args,var_expr_templ = block_assign_fmt_str[block_name]
    if n_pos_args == 4:
        var_expr = var_expr_templ % (loc[1],loc[2],loc[3],loc[4])
    elif n_pos_args == 3:
        var_expr = var_expr_templ % (loc[1],loc[2],loc[3])

    var_name = sym_tbl.new_inst(block_name,loc)

    if n_pos_args == 4:
        stmt = "%s* %s = &%s->%s;" % (var_type,var_name,fab_name,var_expr)
    else:
        stmt = "%s* %s = %s->%s;" % (var_type,var_name,fab_name,var_expr)

    return stmt,var_name

def destroy_config(var_name,block_name,config):
    stmts = []
    Logger.debug(stmts,"disable","disabling %s" % var_name)
    if not block_name in cant_enable:
        stmts.append("%s->setEnable(false);" % var_name)
    return stmts

def make_config(var_name,block_name,config):
    def set_inv(var_name,port,bool_value):
        if not (bool_value == "pos" or bool_value == "neg"):
            raise Exception("unexpected value for %s.%s: %s" % \
                            (var_name,port,bool_value))

        value = "false" if bool_value is "pos" else "false"
        Logger.debug(stmts,"inv","setting <%s.%s.inv> to <%s>" % \
                     (var_name,port,value))
        stmts.append("%s->%s->setInv(%s);" % (var_name,port,value))

    def set_range(var_name,port,scf):
        if not (scf == "med" or scf == "hi" or scf == "low"):
            raise Exception("unexpected scale range for <%s>: <%s>" % \
                            (block_name,scf))

        Logger.debug(stmts,"rng","setting <%s.%s.rng> to <%s>" % \
                     (var_name,port,scf))
        if scf == "med":
            stmts.append("%s->%s->setRange(false,false);" % \
                         (var_name,port))
        elif scf == "hi":
            stmts.append("%s->%s->setRange(false,true);" % \
                        (var_name,port))
        else:
            stmts.append("%s->%s->setRange(true,false);" % \
                        (var_name,port))


    def enable(var_name):
        Logger.debug(stmts,"enable","enabling %s" % var_name)
        stmts.append("%s->setEnable(true);" % var_name)

    stmts = []
    if not block_name in cant_enable:
        enable(var_name)

    if block_name == "multiplier":
        if config.mode == "default":
            pass

        elif config.mode == "vga":
            assert(block_name == "multiplier")
            Logger.debug(stmts,"vga","setting vga mode to true <%s>" % var_name)
            stmts.append("%s->setVga(true);" % var_name)

        else:
            raise Exception("unknown mode <%s>" % config.mode)

        rng = config.scale_mode
        set_range(var_name,"out0",rng)

        if config.has_dac('coeff'):
            assert(block_name == "multiplier")
            value = config.dac('coeff')
            assert(value >= 0 and value <= 255)
            Logger.debug(stmts,"coeff", \
                         "setting gain to [%d] <%s>" % \
                         (value,var_name))

            stmts.append("%s->setGainCode(%d);" % \
                         (var_name,value))

    elif block_name == "integrator":
        assert(config.mode == "default")
        scf_out,scf_in,inv = config.scale_mode
        set_range(var_name,"out0",scf_out)
        set_range(var_name,"in0",scf_in)
        set_inv(var_name,"out0",inv)

        assert(block_name == "integrator")
        value = config.dac("ic")
        assert(value >= 0 and value <= 255)
        Logger.debug(stmts,"ic","setting ic to [%d] <%s>" % (value,var_name))
        stmts.append("%s->setInitialCode(%d);" % \
                     (var_name,value))

    elif block_name == "fanout":
        assert(config.mode == "default")
        inv0,inv1,inv2 = config.scale_mode
        set_inv(var_name,"out0",inv0)
        set_inv(var_name,"out1",inv1)
        set_inv(var_name,"out2",inv2)

    elif block_name == "tile_dac":
        assert(config.mode == "default")
        inv = config.scale_mode
        assert(inv == "pos" or inv == "neg")
        set_inv(var_name,"out0",inv)
        if config.has_dac('in'):
            value = config.dac('in')
            assert(value >= 0 and value <= 255)
            Logger.debug(stmts,
                        "dac","setting dac constant to [%d] <%s>" % \
                        (value,var_name))

            stmts.append("%s->setConstantCode(%d);" % \
                        (var_name,value))
        else:
            assert(config.has_label('in'))

    elif block_name == "due_dac":
        value = config.dac('in')
        assert(value >= 0 and value <= 255)
        Logger.debug(stmts,"dac",\
                     "setting dac constant to [%d] <%s>" % \
                     (value,var_name))
        stmts.append("%s->setConstantCode(%d);" % \
                     (var_name,value))

    elif block_name == "due_adc":
         assert(config.scale_mode == "default")
         assert(config.mode == "default")

    elif block_name == "tile_in":
        assert(config.scale_mode == "default")
        assert(config.mode == "default")

    elif block_name == "chip_in":
        enable(var_name)
        assert(config.scale_mode == "default")
        assert(config.mode == "default")

    elif block_name == "chip_out":
        assert(config.scale_mode == "default")
        assert(config.mode == "default")

    elif block_name == "tile_out":
        assert(config.scale_mode == "default")
        assert(config.mode == "default")


    else:
        raise Exception("unhandled <%s>" % var_name)

    return stmts

def destroy_conn(sym_tbl,sblock,sloc,sport,dblock,dloc,dport):
    stmts = []
    svar = sym_tbl.get_by_loc(sblock,sloc)
    dvar = sym_tbl.get_by_loc(dblock,dloc)
    shwport = block_port[sblock][sport]
    dhwport = block_port[dblock][dport]

    sexpr = "%s->%s" % (svar,shwport)
    dexpr = "%s->%s" % (dvar,dhwport)
    Logger.debug(stmts,"dconn","destroying conn %s to %s" % (sexpr,dexpr))
    stmts.append("Fabric::Chip::Connection(%s,%s).brkConn();"  % \
                 (sexpr,dexpr))
    return stmts

def make_conn(sym_tbl,sblock,sloc,sport,dblock,dloc,dport):
    stmts = []
    svar = sym_tbl.get_by_loc(sblock,sloc)
    dvar = sym_tbl.get_by_loc(dblock,dloc)
    shwport = block_port[sblock][sport]
    dhwport = block_port[dblock][dport]

    sexpr = "%s->%s" % (svar,shwport)
    dexpr = "%s->%s" % (dvar,dhwport)
    Logger.debug(stmts,"conn","connecting %s to %s" % (sexpr,dexpr))
    stmts.append("Fabric::Chip::Connection(%s,%s).setConn();"  % \
        (sexpr,dexpr))

    return stmts

def make_function(header,body):
    body_str = "\n".join(map(lambda stmt: "   %s" % stmt,body))
    body = []
    def write(line):
        body.append(line)

    write("%s {" % header)
    write(body_str)
    write("}")
    return "\n".join(map(lambda stmt: "%s" % stmt,body)) + "\n"

def set_nested_dict(this_dict,key_path,fn,default_value):
    curr_dict = this_dict
    for key in key_path[:-1]:
        if not key in curr_dict:
            curr_dict[key] = {}
        curr_dict = curr_dict[key]

    last_key = key_path[-1]
    if not last_key in curr_dict:
        curr_dict[last_key] = default_value

    curr_dict[last_key] = fn(curr_dict[last_key])


def compute_calibration_stmts(fab_name,circs):
    def add_to_set(x,v):
        x.add(v)
        return x

    insts = set()
    by_block_name = {}
    by_loc = {}
    calib_order = \
                  ["tile_dac","tile_adc","multiplier","fanout","integrator"]

    for circ in circs:
        for block_name, loc,_ in circ.instances():
            if not block_name in calib_order:
                continue

            nargs,fmt_str = block_assign_fmt_str[block_name]
            if nargs == 4:
                calib_stmt = ("%s->"+fmt_str+".calibrate();") % \
                           (fab_name,loc[1],loc[2],loc[3],loc[4])
            else:
                calib_stmt = ("%s->"+fmt_str+"->calibrate();") % \
                           (fab_name,loc[1],loc[2],loc[3])

            insts.add(calib_stmt)
            set_nested_dict(by_block_name,[block_name],
                            lambda x: add_to_set(x,calib_stmt),set())
            set_nested_dict(by_loc, [loc[1],loc[2],loc[3],block_name],
                            lambda x: add_to_set(x,calib_stmt), set())

    return insts,by_block_name,by_loc


def setup_detect_exceptions(circ):
    fab_name = "fabric"
    body = []
    def write(line):
        body.append(line)


    write("bool success = true;")
    blocks_w_exceptions = ["integrator",'tile_adc']
    for block_name, loc, _ in circ.instances():
        if block_name in blocks_w_exceptions:
            raise Exception("write an exception detection routine here")

    write("return success;")
    fun_decl = "bool detect_exception(Fabric * %s)" % fab_name
    return make_function(fun_decl,body)

def make_fabric(circs):
    body = []
    def write(line):
        body.append(line)

    fab_name = "fabric"
    write("Fabric* %s = new Fabric();" % fab_name)
    Logger.debug(body,"*","CALIBRATING")

    insts,by_block_name,by_loc = compute_calibration_stmts(fab_name,circs)

    #total_n = len(insts)
    total_n = 0
    idx = 0
    for chip_no in by_loc:
        by_chip = by_loc[chip_no]
        for tile_no in by_chip:
            by_tile = by_chip[tile_no]
            for slice_no in by_tile:
                by_slice = by_tile[slice_no]
                total_n += 1

    for chip_no in by_loc:
        by_chip = by_loc[chip_no]
        for tile_no in by_chip:
            by_tile = by_chip[tile_no]
            for slice_no in by_tile:
                by_slice = by_tile[slice_no]
                calib_stmt = "%s->chips[%d].tiles[%d].slices[%d].calibrate()" % \
                             (fab_name,chip_no,tile_no,slice_no)
                Logger.debug(body,"calib","%s %d/%d" % \
                             ([chip_no,tile_no,slice_no],idx+1,total_n))
                write("assert(%s);" % calib_stmt)
                idx += 1;


                #for block_name in calib_order:
                #    if block_name in by_slice:
                #        for calib_stmt in by_slice[block_name]:
                #            Logger.debug(body,"calib","%s.%s %d/%d" % \
                #                         (block_name,loc,idx+1,total_n))
                #            write(calib_stmt)
                #            idx += 1;

    #write("fabric->calibrate();")
    Logger.debug(body,"*","CALIBRATED")
    write("return fabric;")

    return make_function("Fabric * new_fabric()", body)

def saf_setup_time_functions(conc_circ,fields):
    body = []
    def write(line):
        body.append(line)

    n_fields = len(fields)
    hw_to_realtime_us = conc_circ.board.meta("hardware_time_us")
    adc_sample_us = conc_circ.board.meta("adc_sample_us")
    adc_delta = conc_circ.board.meta("adc_delta")

    body = []
    write("return compute_samples(time)*%d;" % \
          n_fields)

    size_func = make_function("int compute_size(int time)", body)
    # FUNCTION: compute_samples
    body = []
    write("return ceil(time/%f)/%d+1;" % (conc_circ.tau,adc_sample_us))
    samples_func = make_function("int compute_samples(int time)", body)

    # FUNCTION: compute_hardware_time
    body = []
    write("return time/%f;" % conc_circ.tau)
    hwtime_func = make_function("float compute_hardware_time(int time)", body)

    # FUNCTION: compute_real_time
    body = []
    write("return time/%f*%f*1e-6;" % (conc_circ.tau,hw_to_realtime_us))
    realtime_func = make_function("float compute_real_time(int time)", body)

    return size_func,samples_func,hwtime_func,realtime_func

def saf_setup_write_row(conc_circ,fields,scaling,recover=True):
    body = []
    def write(line):
        body.append(line)

    n_fields = len(fields)
    to_idx = {}
    label_order = []
    for idx,(_,(label,direction)) in enumerate(fields):
        if not label in to_idx:
            to_idx[label] = [None,None]
            label_order.append(label)

        if direction == '-':
            to_idx[label][0] = idx
        else:
            to_idx[label][1] = idx

    adc_sample_us = conc_circ.board.meta("adc_sample_us")
    TIMESCALE = conc_circ.tau * adc_sample_us
    write("float value;")
    write("value = tick*%e;" % TIMESCALE)
    #(3.267596063219 - 0.001592251629*code)/1.2
    SCALE,OFFSET = get_DUE_scale_and_offset()
    write("%s.println(value);" % Logger.interface())
    for label in label_order:
        lo_idx,hi_idx = to_idx[label]
        assert(not lo_idx is None)
        assert(not hi_idx is None)
        scf = 1.0/scaling[label]

        if recover:
            write("value=%e*(%e*data[%d]+%e);" % \
                  (scf,SCALE,hi_idx,OFFSET))
            write("%s.println(value);" % Logger.interface())
        else:
            write("value=data[%d];" % \
                  (hi_idx))
            write("%s.println(value);" % Logger.interface())
            write("value=data[%d];" % \
                  (lo_idx))
            write("%s.println(value);" % Logger.interface())


    write("return %d;" % (len(to_idx.keys())*2))
    value_func = make_function("int write_row(int tick, volatile unsigned short* data)",body)

    body = []
    if recover:
        Logger.data(body,"start_header")
        Logger.data(body,"num,%d" % (n_fields+1))
        Logger.data(body,"field,%d,time" % (0))
        for idx,label in enumerate(label_order):
            Logger.data(body,"field,%d,%s" % (idx+1,label))
        Logger.data(body,"end_header")
    else:
        Logger.data(body,"start_header")
        Logger.data(body,"num,%d" % (n_fields+1))
        Logger.data(body,"field,%d,time" % (0))
        for idx,label in enumerate(label_order):
            Logger.data(body,"field,%d,%s+" % (idx*2+1,label))
            Logger.data(body,"field,%d,%s-" % (idx*2+2,label))
        Logger.data(body,"end_header")

    header_func = make_function("void header()",body)

    return value_func,header_func

def saf_setup_timer_handler(conc_circ,fields):
    body = []
    n_fields = len(fields)
    def write(line):
        body.append(line)

    write("int _pos = *pos;")
    for idx,(chan_no,_) in enumerate(fields):
        write("data[_pos+%d] = ADC->ADC_CDR[%d];" % \
              (idx,chan_no))

    write("*pos = _pos + %d;" % (n_fields))
    write("return _pos + %d >= n;" % n_fields)

    handler_func = make_function(
        "bool handler(volatile unsigned short* data, "+\
        "volatile int* pos, const int n)",
        body)

    return handler_func

def setup_input_functions(conc_circ):
    body = []
    def write(line):
        body.append(line)

    labels = set()
    fab_name = "fab"
    write("int value;")
    for block_name, loc, config in conc_circ.instances():
        for port,(label,scf,label_type) in config.labels():
            if label_type == Labels.OUTPUT:
                continue

            n_pos_args,var_expr_templ = block_assign_fmt_str[block_name]
            if n_pos_args == 4:
                var_name = var_expr_templ % (loc[1],loc[2],loc[3],loc[4])
            elif n_pos_args == 3:
                var_name = var_expr_templ % (loc[1],loc[2],loc[3])

            if block_name == "tile_dac" \
               and label_type == Labels.CONST_INPUT:
                write("value=round(%s*%e*128.0+128.0);" % (label,scf))
                Logger.info(body,"input: ",println=False)
                Logger.info(body,"%s" % label,println=False,literal=False)
                Logger.info(body," -> ",println=False)
                Logger.info(body,"value",literal=False)
                write("%s->%s->setConstantCode(value);" % (fab_name,var_name))
                #set source for constant
                #write("%s->%s->setSource(true,false,false,false);" % \
                #      (fab_name,var_name));
            else:
                raise Exception("unsupported: <%s>" % block_name)

            labels.add(label)


    label_list = list(labels)
    label_list.sort()
    args = ",".join(map(lambda lbl: "float %s" % lbl, label_list))
    func_def = "void set_inputs(Fabric * %s,%s)" % (fab_name,args)
    return label_list,make_function(func_def,body)

def setup_adc_functions(conc_circ,recover=True):
    fields = []
    scaling = {}
    for block_name, loc, config in conc_circ.instances():
        if block_name == "due_adc":
            pos_chan = conc_circ.board.inst_meta(block_name,loc,"chan_pos")
            neg_chan = conc_circ.board.inst_meta(block_name,loc,"chan_neg")
            label = config.label("out")
            scf = config.scf('out')
            fields.append((pos_chan,(label,"+")))
            fields.append((neg_chan,(label,"-")))
            scaling[label] = scf

        elif block_name == "due_dac":
            raise Exception("unsupported")

        else:
            continue

    # time functions
    size_func,samples_func,hwtime_func,realtime_func = \
                            saf_setup_time_functions(conc_circ,fields)

    # FUNCTION: write_row
    write_row_func,header_func =saf_setup_write_row(conc_circ,fields,scaling,
                                                    recover=recover)

    # FUNCTION: handler
    timer_handler_func = saf_setup_timer_handler(conc_circ,fields)

    return  timer_handler_func + header_func + \
        samples_func + hwtime_func + realtime_func + \
        size_func + write_row_func

def setup_chip(conc_circ):
    body = []
    def write(line):
        body.append(line)

    fabric_name = "fab"
    blockvar_map = {}
    block_counts = {}
    sym_tbl = SymbolTable(conc_circ.board)

    for block_name, loc, config in conc_circ.instances():
        decl, var_name = make_decl(sym_tbl,fabric_name,block_name,loc)
        write(decl)
        for stmt in make_config(var_name,block_name,config):
            write(stmt)

        write("")
    for sblock,sloc,sport,dblock,dloc,dport in conc_circ.conns():
        for decl in make_conn(sym_tbl,sblock,sloc,sport,dblock,dloc,dport):
            write(decl)

    write("")
    write("%s->cfgCommit();" % fabric_name)


    return make_function("void configure(Fabric* %s)" % fabric_name, body)

def destroy_chip(conc_circ):
    body = []
    def write(line):
        body.append(line)

    fabric_name = "fab"
    blockvar_map = {}
    block_counts = {}
    sym_tbl = SymbolTable(conc_circ.board)

    for block_name, loc, config in conc_circ.instances():
        decl, var_name = make_decl(sym_tbl,fabric_name,block_name,loc)
        write(decl)
        for stmt in destroy_config(var_name,block_name,config):
            write(stmt)

        write("")
    for sblock,sloc,sport,dblock,dloc,dport in conc_circ.conns():
        for decl in destroy_conn(sym_tbl,sblock,sloc,sport,dblock,dloc,dport):
            write(decl)

    return make_function("void destroy(Fabric* %s)" % fabric_name, body)


def generate_cpp(conc_circ,recover=True):
    body = []
    def write(line):
        body.append(line)

    fab_name = "fabric"

    body.append("#define _DUE")
    body.append("#include <HCDC_DEMO_API.h>")
    body.append("#include <assert.h>")
    body.append("#include \"%s.h\"" % conc_circ.name)
    body.append("")
    write("namespace %s {" % conc_circ.name)
    labels,func = setup_input_functions(conc_circ)
    write(func)
    write(make_fabric([conc_circ]))
    write(setup_chip(conc_circ))
    write(destroy_chip(conc_circ))
    write(setup_adc_functions(conc_circ,recover=recover))
    write(setup_detect_exceptions(conc_circ))
    write("}")
    srccode ="\n".join(body)
    return labels,srccode

def generate_h(conc_circ,labels):
    body = []
    def write(line):
        body.append(line)

    input_fn_args = ",".join(map(lambda lbl: "float %s" % lbl, labels))

    write("#ifndef %s_H" % conc_circ.name)
    write("#define %s_H" % conc_circ.name)
    write("#define _DUE")
    write("#include <HCDC_DEMO_API.h>")
    write("namespace %s {" % conc_circ.name)
    write("  void header();")
    write("  void set_inputs(Fabric * fab, %s);" % input_fn_args)
    write("  int compute_size(int time);")
    write("  float compute_hardware_time(int time_su);")
    write("  float compute_real_time(int time_su);")
    write("  int compute_samples(int time_su);")
    write("  int write_row(int tick,volatile unsigned short* data);")
    write("  bool handler(volatile unsigned short* data, volatile int * pos, const int n);")
    write("  void configure(Fabric* fab);")
    write("  void destroy(Fabric* fab);")
    write("}")
    write("#endif")
    srccode ="\n".join(body)
    return srccode

def generate(conc_circ,recover=True):
    labels,cppsrc = generate_cpp(conc_circ,recover=recover)
    hsrc = generate_h(conc_circ,labels)
    return labels,cppsrc,hsrc

def gde_emit_data(body,name,prefix="",meta=None):
    def write(line):
        body.append(prefix+line)

    Logger.data(body,"DATA_START",indent=prefix)
    Logger.data(body,"start_meta",indent=prefix)
    Logger.data(body,"benchmark,%s" % name,indent=prefix)
    Logger.data(body,"trial,",println=False,indent=prefix)
    Logger.data(body,"trial",literal=False,indent=prefix)
    if not meta is None:
        meta(body,prefix)

    Logger.data(body,"end_meta",indent=prefix)
    write("%s::header();" % name)
    write("int idx=0;")
    Logger.data(body,"start_data",indent=prefix)
    write("for(int tick=0; tick < TICKS; tick++){")
    write("   idx += %s::write_row(tick, &DATA[idx]);" % name)
    write("   assert(idx <= N);")
    write("}")
    Logger.data(body,"end_data",indent=prefix)
    Logger.data(body,"DATA_END",indent=prefix)

# this routine sets the constants that should not change
def gde_configure_chip(body,name,simulation_time):
    def write(line):
        body.append(line)

    Logger.info(body,"runtime: ",println=False)
    Logger.info(body,"%s::compute_real_time(%d)" % (name,simulation_time),
                literal=False,println=False)
    Logger.info(body," us",println=True)
    Logger.debug(body,"exp","-> [[configuring]]")
    write("%s::configure(fabric);" % name)
    Logger.debug(body,"exp","-> compute samples")
    write("TICKS = %s::compute_samples(%d);" % (name,simulation_time))
    Logger.debug(body,"exp","-> number of samples: ",println=False)
    Logger.info(body,"TICKS",literal=False)
    Logger.debug(body,"exp","-> compute data size")
    write("N = %s::compute_size(%d);" % (name,simulation_time))
    Logger.debug(body,"exp","-> data size: ",println=False)
    Logger.info(body,"N",literal=False)

def gde_unconfigure_chip(body,name):
    def write(line):
        body.append(line)

    Logger.debug(body,"exp","-> [[destroying]]")
    write("%s::destroy(fabric);" % name)

def gde_experiment(body,name,labels,assigns={},prefix="",metadata=None):
    def write(line):
        body.append(prefix+line)

    Logger.debug(body,"exp","-> reset position",indent=prefix)
    write("POS = 0;")
    Logger.debug(body,"exp","-> attaching timer interrupt",indent=prefix)
    write("Timer3.attachInterrupt(%s_callback);" % name)
    Logger.debug(body,"exp","-> [[configuring_inputs]]",indent=prefix)
    args = ",".join(map(lambda x: str(assigns[x]), labels))
    write("%s::set_inputs(fabric,%s);" % (name,args))
    Logger.debug(body,"exp","-> [[configured]]",indent=prefix)
    write("fabric->cfgStop();")
    Logger.debug(body,"exp","-> [[simulating]]",indent=prefix)
    write("Timer3.start(DELAY_TIME_US);")
    write("fabric->execStart();")
    write("while (POS != N) {};")
    write("fabric->execStop();")
    Logger.debug(body,"exp","-> [[finished]]",indent=prefix)
    write("Timer3.detachInterrupt();")
    Logger.debug(body,"exp","-> [[finished]]",indent=prefix)
    gde_emit_data(body,name,meta=metadata,prefix=prefix)

def gde_time_series_experiment(experiment,body,name,labels):
    assert(len(labels) == 0)
    gde_experiment(body,name,labels)

def gde_parameter_sweep_experiment(experiment,body,name,labels):
    def write(line):
        body.append(line)

    label_assigns = dict(map(
        lambda ilbl: (ilbl[1],"_%s[idx%d]" % (ilbl[1],ilbl[0])),
        enumerate(labels)))

    indent = "   "
    for idx,label in enumerate(labels):
        values = experiment.values(label)
        value_str = "{%s}" % (",".join(map(lambda v : str(v), values)))
        write("float _%s[%d] = %s;" % (label,len(values),value_str))
        write("int n%d = %d;" % (idx,len(values)))

    for idx,label in enumerate(labels):
        prefix = "" if idx == 0 else "   "*indent
        write((prefix + "for(int idx%d = 0; idx%d < n%d; idx%d++){") % \
              (idx,idx,idx,idx))

    def emit_metadata(body,indent):
        for idx,label in enumerate(labels):
            Logger.data(body,"input,%s," % label,indent=indent,println=False)
            Logger.data(body,"_%s[idx%d]" % (label,idx),indent=indent,literal=False)

    gde_experiment(body,name,labels,
                   assigns=label_assigns,
                   prefix=len(labels)*indent,
                   metadata=emit_metadata)

    for idx,label in enumerate(labels):
        cls_idx = len(labels) - idx - 1
        prefix = "" if cls_idx == 0 else "   "*indent
        write(prefix+"}")


def generate_driver_experiment(name,
                               experiment=experiments.TimeSeriesExperiment(10),
                               labels=[]):
    body = []
    def write(line):
        body.append(line)


    gde_configure_chip(body,name,experiment.simulation_time)
    write("")

    if isinstance(experiment,experiments.TimeSeriesExperiment):
        gde_time_series_experiment(experiment,body,name,labels)

    elif isinstance(experiment,experiments.ParameterSweepExperiment):
        gde_parameter_sweep_experiment(experiment,body,name,labels)

    else:
        raise Exception("unknown experiment <%s>" % experiment)

    gde_unconfigure_chip(body,name)

    exec_fn = make_function("void exec_%s(int trial)" % name, body)

    body = []
    write("if(%s::handler(DATA,&POS,N)){" % name)
    write("   Timer3.stop();")
    write("}")
    handler_fn = make_function("void %s_callback()" % name, body)

    return exec_fn + "\n" + handler_fn

def generate_driver_setup(headers):
    body = []
    def write(line):
        body.append(line)
    write("Serial.begin(115200);")
    write("while(%s.available() == 0) {" % Logger.interface())
    Logger.info(body,"waiting for serial input..",indent="   ")
    write("   delay(300);")
    write("}")
    Logger.info(body,"received serial input..")
    Logger.debug(body,"*","creating new fabric")
    write("fabric = new_fabric();")
    write("N = 0;")
    for name,_ in headers:
        write("if(%s::compute_size(TICKS) > N){" % name)
        write("   N = %s::compute_size(TICKS);" % name)
        write("}")

    write("DATA = new unsigned short[N];")
    return make_function("void setup()",body)

def generate_driver_loop(headers):
    body = []
    def write(line):
        body.append(line)


    write("if(TRIAL_INDEX >= TRIALS){")
    Logger.info(body,"<<EOF>>", println=True)
    write("   delay(300);")
    write("  return;")
    write("}")
    Logger.info(body,"<< Trial ", println=False)
    Logger.info(body,"TRIAL_INDEX", println=False,literal=False)
    Logger.info(body,"/", println=False)
    Logger.info(body,"TRIALS", println=False,literal=False)
    Logger.info(body," >>")
    write("")
    for name,_ in headers:
        write("exec_%s(TRIAL_INDEX);" % name)

    write("")
    write("TRIAL_INDEX += 1;")

    return make_function("void loop()",body)


def generate_driver(experiment,headers,trials=10,circs=[],labels={}):
    body = []
    def write(line):
        body.append(line)


    write("#define _DUE")
    write("#include <HCDC_DEMO_API.h>")
    write("#include <DueTimer.h>")
    write("#include <assert.h>")
    for _,header_file in headers:
        write("#include \"%s\"" % header_file)

    write("")
    write("char HCDC_DEMO_BOARD = %d;" % chip_version())
    write("")
    write("// Trial parameters")
    write("int TICKS = 0;")
    write("const int TRIALS = %d;" % trials)
    write("int TRIAL_INDEX= 0;")
    write("const float DELAY_TIME_US= 1.0;")
    write("")
    write("// Simulation parameters")
    write("volatile int POS = 0;")
    write("int N = 0;")
    write("")
    write("// Simulation data")
    write("volatile unsigned short * DATA;")
    write("Fabric * fabric;")
    write("")
    write("/* CALIBRATE FABRIC FOR ALL EXPERIMENTS*/")
    write(make_fabric(circs))
    write("")
    write("/* EXPERIMENT FUNCTIONS */")
    for name,_ in headers:
        write(generate_driver_experiment(name,experiment,labels[name]))
        write("")

    write("/* MAIN SETUP*/")
    setup_fn = generate_driver_setup(headers)
    write(setup_fn)
    write("/* MAIN LOOP */")
    loop_fn = generate_driver_loop(headers)
    write(loop_fn)
    return "\n".join(map(lambda x : str(x), body))


def write_file(experiment,srcfiles,output,
               parent_dir="",trials=10,circs=[]):

    abs_path = lambda x : "%s/%s/%s" % (parent_dir,output,x)

    if parent_dir != "" and not os.path.exists(parent_dir):
        os.mkdir(parent_dir)

    if not os.path.exists(abs_path("")):
        os.mkdir(abs_path(""))

    headers= []
    label_map = {}
    for labels,name, cpp_source, h_source in srcfiles:
        header_file = "%s.h" % name
        cpp_file = "%s.cpp" % name
        with open(abs_path(cpp_file),'w') as fh:
            fh.write(cpp_source)

        with open(abs_path(header_file),'w') as fh:
            fh.write(h_source)

        label_map[name] = labels
        headers.append((name,header_file))

    driver_code = generate_driver(experiment,headers,
                                  circs=circs, \
                                  trials=trials,\
                                  labels=label_map)
    runner_file = "%s.ino" % output
    with open(abs_path(runner_file),'w') as fh:
        fh.write(driver_code)
