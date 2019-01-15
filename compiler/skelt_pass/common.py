
class NoiseEnv:

  def __init__(self):
    self._visited = {}

  def visit(self,blkname,loc,port):
    self._visited[(blkname,loc,port)] = True

  def visited(self,blkname,loc,port):
    return (blkname,loc,port) in self._visited


