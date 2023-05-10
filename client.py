import socket
import time
import threading
from DSComm import DSComm
from DSMessage import DSMessage

#This function is required for the middleware to communicate the data back to the client.
def listen_for_response(sock):
    comm = DSComm(sock)
    while True:
        mess = comm.recvMessage()
        if mess:
            tipe = mess.getType()
            data = mess.getData().decode('utf-8')
            #If response does not warrant data to be returned, or if an error occured
            if tipe == 'OKOK' or tipe == 'ERRO':
                print(tipe)
                print(data)
                break
            #Return error if unknown reason for failure.
            else:
                print('Unknown Error :/')
                print(tipe + ':' + data)
                break
    print('Complete')

def ClientProtocol(sock):
    while True:
        msg = DSMessage()
        line = input('Enter Command: ')
        msg.setType(line[:4])
        d = line[4:]
        msg.setData(d.encode('utf-8'))
        #sends message to middleware
        comm = DSComm(sock)
        comm.sendMessage(msg)
        listen_for_response(sock)

if __name__ == '__main__':
    mainserv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        mainserv.connect(('localhost', 50000))
        print('Connected to server')
    except:
        print('Could not connect to server')
    while True:
        ClientProtocol(mainserv)
    mainserv.close()
    