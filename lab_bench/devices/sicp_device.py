
class SICPDevice:

    def __init__(self,ipaddr,port):
        self._ip = ipaddr
        self._port = port
        self._buf = bytearray([])

    def setup(self):
        self._sock = SocketConnect(self._ip,self._port)

    def _flush(self):
        readable, writable, exceptional = select.select([self._sock],
                                                        [],
                                                        [],
                                                        1.0)
        if readable:
            data = self._sock.recv(1024)
        else:
            return

    def _recvall(self,eom=b'\n'):
        total_data=[];
        data=self._buf
        self._buf = bytearray([])
        done = False
        while not done:
            if eom in data:
                eom_idx = data.find(eom)
                assert(eom_idx >= 0)
                seg = data[:eom_idx]
                self._buf = data[eom_idx+len(eom):]
                total_data.append(seg)
                done = True
                continue
            else:
                total_data.append(data)

            data=self._sock.recv(4096)

        ba = bytearray([])
        for datum in total_data:
            ba += datum

        return ba


    def write(self,cmd):
        try :
            #Send cmd string
            print("-> %s" % cmd)
            self._sock.sendall(bytes(cmd,'UTF-8'))
            self._sock.sendall(b'\n')
            time.sleep(0.1)
        except socket.error:
            #Send failed
            print(socket.error)
            print ('send failed <%s>' % cmd)
            sys.exit()

    def query(self,cmd,decode='UTF-8',eom=b'\n\r>>'):
        self._flush()
        self.write(cmd)
        reply = self._recvall(eom=eom)
        if not decode is None:
            return reply.decode(decode)
        else:
            return reply

    def get_identifier(self):
        return self.query("*IDN?")
