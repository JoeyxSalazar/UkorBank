'''
Created on Feb 15, 2023

@author: nigel
'''
import socket
from DSMessage import DSMessage

class DSComm(object):
    '''
    classdocs
    '''
    BUFSIZE = 8196



    def __init__(self, s : socket = -1):
        '''
        Constructor
        '''
        self._sock = s
        
    def _loopRecv(self, size: int):
        data = bytearray(b" "*size)
        mv = memoryview(data)
        while size:
            rsize = self._sock.recv_into(mv,size)
            mv = mv[rsize:]
            size -= rsize
        return data
        
    def sendMessage(self, m: DSMessage):
        data = m.marshal()
        self._sock.sendall(data)
    
    def recvMessage(self) -> DSMessage:
        try:
            m = DSMessage()
            mtype = self._loopRecv(4)
            size = self._loopRecv(4)
            data = self._loopRecv(int(size.decode('utf-8')))
            params = b''.join([mtype,size,data])
            m.unmarshal(params)
        except Exception:
            raise Exception('bad getMessage')
        else:
            return m
    
    def close(self):
        self._sock.close()