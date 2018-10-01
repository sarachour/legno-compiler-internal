import blocks as hw
import props
import ops


class AbsLabel:

    def __init__(self,kind,name):
        assert(isinstance(name,str))
        self._name = name
        self._type = kind

    @property
    def type(self):
        return self._type

    @property
    def name(self):
        return self._name

    def __repr__(self):
        return "%s.%s" % (self._type,self._name)

class ADCLabel(AbsLabel):

    def __init__(self,name):
        AbsLabel.__init__(self,"adc",name)


class InstLabel(AbsLabel):

    def __init__(self,name,inst=0):
        AbsLabel.__init__(self,"inst:%d"%inst,name)


class RefLabel(AbsLabel):

    def __init__(self,name,ref=0):
        AbsLabel.__init__(self,"ref:%d"%ref,name)

class AbsCircuit:


    def __init__(self):
        self._labels = {}

    def add(self,label,subcirc):
        assert(isinstance(label,AbsLabel))
        assert(not label in self._labels)
        self._labels[label] = subcirc

    def remove(self,label):
        del self._labels[label]

    def feasible(self):
        counts = {}
        for subcirc in self._labels.values():
            blocks = subcirc.reduce(lambda x : x.args() \
                                    if x.name == 'block' else None)

            for args in blocks:
                if not args['block'] in counts:
                    counts[args['block']] = 0

                counts[args['block']] += 1

        # TODO: check to make sure the components exist.
        return True


    def reduce(self,xform):
        for subcirc in self._labels.values():
            for result in  subcirc.reduce(xform):
                yield result


    def get_references(self,name):
        for label,ast in self._labels.items():
            if isinstance(label,RefLabel) and label.name == name:
                yield label,ast


    def num_references(self,name):
        return len(list(self.get_references(name)))


    def get_instances(self,name):
        for label,ast in self._labels.items():
            if isinstance(label,InstLabel) and label.name == name:
                yield label,ast


    def num_instances(self,name):
        return len(list(self.get_instances(name)))

    @property
    def labels(self):
        return self._labels.keys()

    def copy(self):
        circ = AbsCircuit()
        for label,subcirc in self._labels.items():
            circ.add(label,subcirc.copy())

        return circ

    def __repr__(self):
        st = ""
        for label,subc in self._labels.items():
            st += "=> %s\n" % label
            st += subc.to_string()

        return st

class AbsNode:

    def __init__(self,name,parent=None):
        self._name = name
        self._children = []
        self._parent = parent

    @property
    def name(self):
        return self._name

    def ancestor(self,node):
        if node == self:
            return True
        elif not self._parent is None:
            return self._parent.ancestor(node)
        else:
            return False

    def add(self,child):
        assert(not child is None)
        if not (child._parent is None):
            print("==== Child =====\n%s\n\n" % child.to_string())
            print("==== Old Parent =====\n%s\n\n" %
                  child._parent.to_string())
            print("==== New Parent =====\n%s\n\n" % self.to_string())
            raise Exception("child already has parent")

        child._parent = self
        assert(not self.ancestor(child))
        self._children.append(child)

    @property
    def parent(self):
        return self._parent

    @property
    def children(self):
        for ch in self._children:
            yield ch

    def remove_children(self):
        self._children = []

    def remove_child(self,n):
        self._children = list(filter(lambda x : not n == x,
                                     self._children))
    @parent.setter
    def parent(self,new_p):
        assert(new_p is None or isinstance(new_p,AbsNode))
        self._parent = new_p

    def find(self,predicate):
        if predicate(self):
            return self

        else:
            for ch in self._children:
                result = ch.find(predicate)
                if not result is None:
                    return result

            return None

    def reduce(self,xform):
        subresults = []
        for ch in self._children:
            subresults += ch.reduce(xform)

        if not xform(self) is None:
            return [xform(self)] + subresults
        else:
            return subresults

    def args(self):
        raise NotImplementedError

    def copy(self,new_node):
        for ch in self._children:
            new_ch = ch.copy()
            new_node.add(new_ch)

        return new_node

    def to_string(self,indent=0):
        st = " "*indent if indent > 0 else ""
        st += self._name + " " + str(self.args()) +"\n"
        for ch in self._children:
            st += ch.to_string(indent=indent+1)
        return st

    def __repr__(self,with_args=False):
        chstr = " ".join(map(lambda ch: str(ch), self._children))
        argsstr = str(self.args()) if with_args else ""
        return "(%s %s %s)" % (self.name,argsstr,chstr)


class BlockNode(AbsNode):

    def __init__(self,block_name,mode):
        AbsNode.__init__(self,"block")
        self._block = block_name
        self._mode = mode

    @property
    def block(self):
        return self._block

    @property
    def mode(self):
        return self._mode

    def copy(self):
        bn = BlockNode(self._block,self._mode)
        return AbsNode.copy(self,bn)

    def add(self,input_node):
        assert(isinstance(input_node,InputNode))
        AbsNode.add(self,input_node)

    def args(self):
        return {'block':self._block,'mode':self._mode}

class InputNode(AbsNode):

    def __init__(self,input_name,expr):
        AbsNode.__init__(self,"input")
        self._input = input_name
        self._expr = expr

    @property
    def input(self):
        return self._input

    @property
    def expr(self):
        return self._expr

    def copy(self):
        ino =InputNode(self._input,self._expr)
        return AbsNode.copy(self,ino)

    def add(self,output_node):
        assert(isinstance(output_node,OutputNode) or \
               isinstance(output_node,StubNode) or \
               isinstance(output_node,ConnNode))
        AbsNode.add(self,output_node)

    def args(self):
        return {'input':self._input,'expr':self._expr}


class ConnNode(AbsNode):

    def __init__(self,label):
        AbsNode.__init__(self,"conn")
        self._label = label

    @property
    def expr(self):
        return self._expr

    def copy(self):
        stub = ConnNode(self._label)
        return AbsNode.copy(self,stub)

    def add(self,node):
        raise Exception("stub cannot have any children")

    def args(self):
        return {'label':self._label}




class StubNode(AbsNode):

    def __init__(self,expr):
        AbsNode.__init__(self,"stub")
        self._expr = expr

    @property
    def expr(self):
        return self._expr

    def copy(self):
        stub = StubNode(self._expr)
        return AbsNode.copy(self,stub)

    def add(self,node):
        raise Exception("stub cannot have any children")

    def args(self):
        return {'expr':self._expr}


class OutputNode(AbsNode):

    def __init__(self,output_name,expr):
        AbsNode.__init__(self,"output")
        self._output = output_name
        self._expr = expr

    @property
    def block(self):
        return self._children[0]

    @property
    def output(self):
        return self._output

    @property
    def expr(self):
        return self._expr

    def add(self,block_node):
        assert(isinstance(block_node,BlockNode))
        assert(len(self._children) == 0)
        AbsNode.add(self,block_node)


    def copy(self):
        ono = OutputNode(self._output,self._expr)
        return AbsNode.copy(self,ono)

    def args(self):
        return {'output':self._output,'expr':self._expr}



