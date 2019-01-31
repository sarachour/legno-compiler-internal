import os
import colorlover

def undef_to_one(v):
  return 1.0 if v is None else v

class Shader:
  IGNORE = "ignore"
  ERROR = "error"

  def __init__(self):
    self._min = 0
    self._max = max(self.all_values())*2
    self._n = 500
    sch = colorlover.scales['9']['seq']['BuPu']
    self._scheme = colorlover.interp(sch,500)

  @staticmethod
  def get_shader(circ,method):
    if method == 'interval':
      return IntervalShader(circ)
    elif method == 'scaled-interval':
      return ScaledIntervalShader(circ)
    elif method == 'scale-factor':
      return ScaleFactorShader(circ)
    elif method == 'gen-delay':
      return GenDelayShader(circ)
    elif method == 'prop-delay':
      return PropDelayShader(circ)
    elif method == 'delay-mismatch':
      return DelayMismatchShader(circ)
    elif method == 'gen-noise':
      return GenNoiseShader(circ)
    elif method == 'prop-noise':
      return PropNoiseShader(circ)
    elif method == 'gen-bias':
      return GenBiasShader(circ)
    elif method == 'prop-bias':
      return PropBiasShader(circ)
    elif method is None:
      return GenericShader()
    else:
      raise Exception("unknown shader: <%s>" % method)


  def to_color(self,value):
    if self._max == self._min:
      return "#fffffff"

    pct = (value-self._min)/(self._max-self._min)
    bin_no = min(int(pct*self._n), self._n-1)
    color = self._scheme[bin_no]
    r,g,b = colorlover.to_numeric(colorlover.to_rgb([color]))[0]
    hexval = "#{0:02x}{1:02x}{2:02x}".format(int(r),int(g),int(b))
    return hexval

  def white(self):
    return "#ffffff"

  def red(self):
    return "#f8585a"

  def get_block_color(self,name,loc):
    value = self.get_block_value(name,loc)
    if value == Shader.IGNORE:
      return self.white()
    elif value == Shader.ERROR:
      return self.red()
    else:
      return self.to_color(value)

  def get_port_color(self,name,loc,port):
    value = self.get_port_value(name,loc,port)
    if value == Shader.IGNORE:
      return self.white()
    elif value == Shader.ERROR:
      return self.red()
    else:
      return self.to_color(value)

  def is_value(self,v):
    return not v == Shader.IGNORE and \
      not v == Shader.ERROR

  def all_values(self):
    raise NotImplementedError

  def get_block_value(self,name,loc):
    return Shader.IGNORE

  def get_port_value(self,name,loc,port):
    return Shader.IGNORE

class CircShader(Shader):

  def __init__(self,circ):
    self.circ = circ
    Shader.__init__(self)

  def all_values(self):
    for block_name,loc,cfg in self.circ.instances():
      value = self.get_block_value(block_name,loc)
      if self.is_value(value):
        yield value
      block = self.circ.board.block(block_name)
      for port in block.inputs + block.outputs:
        value = self.get_port_value(block_name,loc,port)
        if self.is_value(value):
          yield value


class GenericShader(Shader):

  def __init__(self):
    Shader.__init__(self)

  def all_values(self):
    yield 0


class DelayMismatchShader(CircShader):

  def __init__(self,circ):
    CircShader.__init__(self,circ)

  def get_port_value(self,name,loc,port):
    cfg = self.circ.config(name,loc)
    ival = cfg.delay_mismatch(port)
    if ival is None:
      return Shader.ERROR
    else:
      return ival


class PropDelayShader(CircShader):

  def __init__(self,circ):
    CircShader.__init__(self,circ)

  def get_port_value(self,name,loc,port):
    cfg = self.circ.config(name,loc)
    ival = cfg.propagated_delay(port)
    if ival is None:
      return Shader.ERROR
    else:
      return ival.bound

class PropBiasShader(CircShader):

  def __init__(self,circ):
    CircShader.__init__(self,circ)


  def get_port_value(self,name,loc,port):
    cfg = self.circ.config(name,loc)
    ival = cfg.propagated_bias(port)
    if ival is None:
      return Shader.ERROR
    else:
      return ival.bound



class GenBiasShader(CircShader):

  def __init__(self,circ):
    CircShader.__init__(self,circ)

  def get_port_value(self,name,loc,port):
    cfg = self.circ.config(name,loc)
    ival = cfg.generated_bias(port)
    if ival is None:
      return Shader.ERROR
    else:
      return ival.bound


class PropNoiseShader(CircShader):

  def __init__(self,circ):
    CircShader.__init__(self,circ)

  def get_port_value(self,name,loc,port):
    cfg = self.circ.config(name,loc)
    ival = cfg.propagated_noise(port)
    if ival is None:
      return Shader.ERROR
    else:
      return ival.bound



class GenNoiseShader(CircShader):

  def __init__(self,circ):
    CircShader.__init__(self,circ)

  def get_port_value(self,name,loc,port):
    cfg = self.circ.config(name,loc)
    ival = cfg.generated_noise(port)
    if ival is None:
      return Shader.ERROR
    else:
      return ival.bound


class GenDelayShader(CircShader):

  def __init__(self,circ):
    CircShader.__init__(self,circ)

  def get_port_value(self,name,loc,port):
    cfg = self.circ.config(name,loc)
    ival = cfg.generated_delay(port)
    if ival is None:
      return Shader.ERROR
    else:
      return ival.bound

class ScaleFactorShader(CircShader):

  def __init__(self,circ):
    CircShader.__init__(self,circ)

  def get_port_value(self,name,loc,port):
    cfg = self.circ.config(name,loc)
    scf = cfg.scf(port)
    if scf is None:
      return Shader.ERROR
    else:
      return scf


class ScaledIntervalShader(CircShader):

  def __init__(self,circ):
    CircShader.__init__(self,circ)

  def get_port_value(self,name,loc,port):
    cfg = self.circ.config(name,loc)
    ival = cfg.interval(port)
    scf = cfg.scf(port)
    if ival is None or scf is None:
      return Shader.ERROR
    else:
      return ival.bound


class IntervalShader(CircShader):

  def __init__(self,circ):
    CircShader.__init__(self,circ)

  def get_port_value(self,name,loc,port):
    cfg = self.circ.config(name,loc)
    ival = cfg.interval(port)
    scf = cfg.scf(port)
    if ival is None or scf is None:
      return Shader.ERROR
    else:
      return ival.bound/scf

class DotFileCtx:

  def __init__(self,circ,method):
    self._node_stmts = []
    self._conn_stmts = []
    self.circ = circ
    self._id_to_data = {}
    self._blockloc_to_id = {}
    self.shader = Shader.get_shader(circ,method)

  def bind(self,name,loc,config):
    ident = len(self._id_to_data)
    self._id_to_data[ident] = {
      'name': name,
      'loc': loc,
      'config': config
    }
    self._blockloc_to_id[(name,loc)] = ident

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


def build_environment(circ,color_method=None):
  env = DotFileCtx(circ,method=color_method)
  for block_name,loc,config in circ.instances():
      env.bind(block_name,loc,config)

  return env

def build_port(env,block_name,block_loc,port):
  color = env.shader.get_port_color(block_name,block_loc,port)
  port_handle = env.port_handle(block_name,block_loc,port)
  caption_handle = "%s_caption" % port_handle

  value = env.shader.get_port_value(block_name,block_loc,port)
  if isinstance(value,float):
    value = '%.03e' % value
    env.qn('%s [' % caption_handle,1)
    env.qn('shape=plaintext',2)
    env.qn('label=<%s>' % (value), 2)
    env.qn(']',1)
    env.qc('%s->%s [style=dashed]' % (caption_handle,port_handle))

  env.qn('%s [' % port_handle,1)
  env.qn('shape=invtriangle',2)
  env.qn('fillcolor=\"%s\"' % color,2)
  env.qn('style=filled',2)
  env.qn("label=<%s>" % (port),2)
  env.qn(']',1)
  return port_handle

def build_body(env,block_name,block_loc,cfg):
  body = '''
    <table border="0">
    <tr><td>{block_name}</td><td>{block_loc}</td></tr>
    <tr>
    <td><font color="#5D6D7E">{scale_mode}</font></td>
    <td><font color="#5D6D7E">{comp_mode}</font></td>
    </tr>
    </table>
    '''

  params = {
      'block_name':block_name,
      'block_loc':block_loc,
      'scale_mode':cfg.scale_mode,
      'comp_mode':cfg.comp_mode
  }
  color = env.shader.get_block_color(block_name,block_loc)
  html = body.format(**params)
  body_handle = env.body_handle(block_name,block_loc)
  env.qn('%s [' % body_handle,1)
  env.qn('shape=record',2)
  env.qn('fillcolor=\"%s\"' % color,2)
  env.qn('style=filled',2)
  env.qn('shape=record',2)
  env.qn('label=<%s>' % html,2)
  env.qn(']',1)
  return body_handle

def build_block(env,block_name,block_loc,cfg):
    blkidx = env.get_id(block_name,block_loc)
    block = env.circ.board.block(block_name)
    env.qn('subgraph cluster%d {' % blkidx)
    env.qn('style=filled')
    env.qn('color=lightgrey')
    env.qn('rank=same')
    body_handle = env.body_handle(block_name,block_loc)
    for inp in block.inputs:
        port_handle = build_port(env,block_name,block_loc,inp)
        env.qc('%s -> %s' %(port_handle,body_handle),1)

    build_body(env,block_name,block_loc,cfg)

    for out in block.outputs:
        port_handle = build_port(env,block_name,block_loc,out)
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
    body = '''
    <table border="0">
    <tr><td>val: {value:.3e}</td></tr>
    <tr><td><font color="#5D6D7E">scf:{scf:.3e}</font></td></tr>
    </table>
    '''

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
