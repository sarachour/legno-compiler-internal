import os
import colorlover

def undef_to_one(v):
  return 1.0 if v is None else v

class Shader:

  def __init__(self):
    self._min = 0
    self._max = max(self.all_values())*2
    self._n = 500
    sch = colorlover.scales['9']['seq']['BuPu']
    self._scheme = colorlover.interp(sch,500)

  def all_values(self):
    raise NotImplementedError

  def to_color(self,value):
    pct = (value-self._min)/(self._max-self._min)
    bin_no = min(int(pct*self._n), self._n-1)
    color = self._scheme[bin_no]
    r,g,b = colorlover.to_numeric(colorlover.to_rgb([color]))[0]
    hexval = "#{0:02x}{1:02x}{2:02x}".format(int(r),int(g),int(b))
    return hexval

class IntervalShader(Shader):

  def __init__(self,circ):
    self._circ = circ
    Shader.__init__(self)

  def all_values(self):
    for name,loc,cfg in self._circ.instances():
      for port,ival in cfg.intervals().items():
          value = ival.spread*undef_to_one(cfg.scf(port))
          print("%s[%s].%s = %s" % (name,loc,port,value))
          yield value

  def get_port_color(self,name,loc,port):
    cfg = self._circ.config(name,loc)
    ival = cfg.interval(port)
    return self.to_color(ival.spread*cfg.scf(port))

class DotFileCtx:

  def __init__(self,circ):
    self._node_stmts = []
    self._conn_stmts = []
    self.circ = circ
    self._id_to_data = {}
    self._blockloc_to_id = {}
    self._colors = IntervalShader(circ)

  def bind(self,name,loc,config):
    ident = len(self._id_to_data)
    self._id_to_data[ident] = {
      'name': name,
      'loc': loc,
      'config': config
    }
    self._blockloc_to_id[(name,loc)] = ident

  def get_port_color(self,name,loc,port):
    return self._colors.get_port_color(name,loc,port)

  def get_block_color(self,name,loc):
    return '#1effee'

  def get_id(self,name,loc):
    return self._blockloc_to_id[(name,loc)]

  def qn(self,stmt,indent=0):
    prefix = "  "*indent if indent > 0 else ""
    self._node_stmts.append(prefix + stmt)

  def qc(self,stmt,indent=0):
    prefix = "  "*indent if indent > 0 else ""
    self._conn_stmts.append(prefix + stmt)

  def program(self):
    stmts = self._node_stmts + self._conn_stmts
    prog = "digraph circuit {\n%s\n}" % ("\n".join(stmts))
    return prog

  def body_handle(self,name,loc):
    blkidx = self.get_id(name,loc)
    return "block%d" % blkidx

  def port_handle(self,name,loc,port):
    blkidx = self.get_id(name,loc)
    blkhandle = self.body_handle(name,loc)
    block = self.circ.board.block(name)
    if port in block.inputs:
        return "%s_inp%d" % (blkhandle, block.inputs.index(port))
    elif port in block.outputs:
        return "%s_out%d" % (blkhandle, block.outputs.index(port))
    else:
        raise Exception("can't find port: %s" % str(port))


def build_environment(circ,color_method = None):
  env = DotFileCtx(circ)
  for block_name,loc,config in circ.instances():
      '''
      colors = {}
      for input_port in blk.inputs:
        colors[input_port] = '"#ed13fe"'
      for output_port in blk.outputs:
        colors[output_port] = '"#000eff"'
      colors['body'] = '"#eef1ee"'
      '''
      env.bind(block_name,loc,config)

  return env
 

def build_block(env,block_name,block_loc,cfg):
    body = '''
    <table border="0">
    <tr><td>{block_name}</td><td>{block_loc}</td></tr>
    <tr>
    <td><font color="#5D6D7E">{scale_mode}</font></td>
    <td><font color="#5D6D7E">{comp_mode}</font></td>
    </tr>
    </table>
    '''
    blkidx = env.get_id(block_name,block_loc)
    block = env.circ.board.block(block_name)
    env.qn('subgraph cluster%d {' % blkidx)
    env.qn('style=filled')
    env.qn('color=lightgrey')
    env.qn('rank=same')
    for inp in block.inputs:
        color = env.get_port_color(block_name,block_loc,inp)
        port_handle = env.port_handle(block_name,block_loc,inp)
        body_handle = env.body_handle(block_name,block_loc)
        env.qn('%s [' % port_handle)
        env.qn('shape=invtriangle',2)
        env.qn('fillcolor=\"%s\"' % color,2)
        env.qn('style=filled',2)
        env.qn("label=<%s>" % (inp),2)
        env.qn(']')
        env.qc('%s -> %s' %(port_handle,body_handle),1)

    params = {
        'block_name':block_name,
        'block_loc':block_loc,
        'scale_mode':cfg.scale_mode,
        'comp_mode':cfg.comp_mode
    }
    html = body.format(**params)
    body_handle = env.body_handle(block_name,block_loc)
    env.qn('%s [' % body_handle,1)
    env.qn('shape=record',2)
    env.qn('fillcolor=\"%s\"' % \
           env.get_block_color(block_name,block_loc),2)
    env.qn('style=filled',2)
    env.qn('shape=record',2)
    env.qn('label=<%s>' % html,2)
    env.qn(']',1)

    for out in block.outputs:
        color = env.get_port_color(block_name,block_loc,out)
        port_handle = env.port_handle(block_name,block_loc,out)
        body_handle = env.body_handle(block_name,block_loc)
        env.qn('%s [' % port_handle)
        env.qn('shape=invtriangle',1)
        env.qn("label=<%s>" % (out),1)
        env.qn('fillcolor=\"%s\"' % color,1)
        env.qn('style=filled',1)
        env.qn(']')
        env.qc('%s -> %s' %(body_handle,port_handle),1)

    env.qn("}")

def build_label(env,block,loc,cfg,port,math_label,kind):
  body = '''
  <table border="0">
  <tr><td>{kind} {label}</td></tr>
  <tr><td><font color="#5D6D7E">scf:{scf:.3e}</font></td></tr>
  <tr><td><font color="#5D6D7E">tau:{tau:.3e}</font></td></tr>
  </table>
  '''
  port_handle = env.port_handle(block,loc,port)
  label_handle = "%s_label" % (port_handle)
  kind = kind.value
  scf = undef_to_one(cfg.scf(port))
  #label = "%s %s*%.3e t:%.3e" % (kind,math_label,scf,self.tau)
  params = {
      'kind':kind,
      'label':math_label,
      'scf':scf,
      'tau':env.circ.tau
  }
  label = body.format(**params)
  env.qn("%s [" % (label_handle))
  env.qn("shape=cds",2)
  env.qn("label=<%s>" % label,2)
  env.qn("]")
  env.qc("%s->%s [penwidth=3.0 color=black]" % (port_handle,label_handle),1)


def build_value(env,block,loc,cfg,port,value):
    body = '{value:.3f}*{scf:.3f}'
    port_handle = env.port_handle(block,loc,port)
    value_handle = "%s_value" % (port_handle)

    scf = undef_to_one(cfg.scf(port))
    params = {
        'value': value, 'scf': scf
    }
    label = body.format(**params)
    env.qn("%s [" % (value_handle))
    env.qn("shape=cds",2)
    env.qn('label=<%s>' % label,2)
    env.qn("]")
    env.qc("%s->%s [penwidth=3.0 color=red]" % (value_handle,port_handle),1)

def write_graph(circ,filename,color_method=None,write_png=False):
    env = build_environment(circ,color_method)
    for block,loc,cfg in circ.instances():
        build_block(env,block,loc,cfg)

        for port,math_label,kind in cfg.labels():
            build_label(env,block,loc,cfg,port,math_label,kind)

        for port,value in cfg.values():
            build_value(env,block,loc,cfg,port,value)

    for sblk,sloc,sport,dblk,dloc,dport in circ.conns():
      src_handle = env.port_handle(sblk,sloc,sport)
      dest_handle = env.port_handle(dblk,dloc,dport)
      env.qc("%s -> %s [penwidth=3.0 color=blue]" % (src_handle,dest_handle),1)

    prog = env.program()
    with open(filename,'w') as fh:
        fh.write(prog)

    if write_png:
        assert(".dot" in filename)
        basename = filename.split(".dot")[0]
        imgname = "%s.png" % basename
        cmd = "dot -Tpng %s -o %s" % (filename,imgname)
        os.system(cmd)
