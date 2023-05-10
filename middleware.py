import socket
import time
import threading
import re
from DSMessage import DSMessage
from DSComm import DSComm

logged_in = False
access_checking = True
user_id = ""
checking_num = ""
savings_num = ""


def send_data(type, data, sock):
    mess = DSMessage()
    mess.setType(type)
    if isinstance(data, bytes) == False:
        mess.setData(data.encode('utf-8'))
    else:
        mess.setData(data)
    comm = DSComm(sock)
    comm.sendMessage(mess)

def receive_data(dbsock):
    comm = DSComm(dbsock)
    while True:
        mess = comm.recvMessage()
        if mess:
            tipe = mess.getType()
            data = mess.getData().decode('utf-8')
            print(tipe,':',data)
            if tipe == 'OKOK' or tipe == 'ERRO':
                print()
                return tipe, data
            
def Menu(clisock):
    with open('menu.txt', 'r') as file:
        contents = file.read()
        send_data('OKOK', contents ,clisock)
    return

#This function handles whether or not a user is logged in, prevents user from sending commands if not logged in or signing up
def ExtractCommand(tipe):
    global logged_in
    if logged_in or tipe == 'LGIN' or tipe == 'SIGN':
        return tipe
    else:
        return 'Retry'
    
def LoginProtocol(data, clientserv, dbserv):
    #data should be formatted as username:password
    global logged_in
    global user_id
    global checking_num
    global savings_num
    parts = data.split(':')
    print(parts) #only for testing purposes
    if len(parts) == 2:
        try:
            send_data('LGIN', data, dbserv)
            #user_data needs to contain user_id, checking_id, and savings_id
            #if the user does not have a savings account, send 'NULL'
            tipe, user_data = receive_data(dbserv)
            #Login successful, set globals and send message to client notifying them of success
            if tipe == 'OKOK' or tipe == 'DATA':
                logged_in = True
                creds = user_data.split(':')
                if len(creds) == 3:
                    user_id, checking_num, savings_num = creds[0], creds[1], creds[2]
                else:
                    send_data('ERRO', 'Error retrieving credentials', clientserv)
                    logged_in = False
                    return
                send_data('OKOK', 'Login Success!', clientserv)
            else:
                send_data('ERRO', user_data, clientserv)
        except:
            send_data('ERRO', 'Error communicating with Database', clientserv)
        pass
    else:
        send_data('ERRO', 'Invalid Format', clientserv)
    pass

def SignUpProtocol(data, clientserv, dbserv):
    #data should be aacount_type:username:password
    creds = data.split(':')
    if len(creds) != 3:
        send_data('ERRO', 'Invalid sign-up format', clientserv)
    else:
        send_data('SIGN', data, dbserv)
        tipe, response = receive_data(dbserv)
        if tipe == 'OKOK':
            send_data('OKOK', 'Account Created!', clientserv)
        else:
            send_data('ERRO', 'Error creating your account.', clientserv)
    pass

def OpenAccountProtocol(data, clientserv, dbserv):
    #data should be type
    global checking_num
    global savings_num
    global user_id
    if data != 'CHCK' or data != 'SAVI':
        send_data('ERRO', 'Invalid Account Type', clientserv)
    elif data == 'CHCK' and (checking_num == '' or checking_num == 'NULL'):
        data = user_id + ':' + data
        send_data('OPEN', data, dbserv)
        tipe, response = receive_data(dbserv)
        if tipe == 'OKOK':
            send_data('OKOK', 'Account Created!', clientserv)
        else:
            send_data('ERRO', 'Error creating account', clientserv)
        pass
    elif data == 'SAVI' and (savings_num == '' or savings_num == 'NULL'):
        data = user_id + ':' + data
        send_data('OPEN', data, dbserv)
        tipe, response = receive_data(dbserv)
        if tipe == 'OKOK':
            send_data('OKOK', 'Account Created!', clientserv)
        else:
            send_data('ERRO', 'Error creating account', clientserv)
        pass
    else:
        send_data('ERRO', 'Account already exists! Otherwise, unknown error', clientserv)  
    pass


def LogoutProtocol(data, clientserv, dbserv):
    global logged_in
    global user_id
    global checking_num
    global savings_num
    logged_in = False
    user_id = ""
    checking_num = ""
    savings_num = ""
    send_data('OKOK', 'Logout Success!', clientserv)
    pass

def StatementProtocol(data, clientserv, dbserv):
    pass

def CheckingProtocol(data, clientserv, dbserv):
    global access_checking
    global checking_num
    if checking_num != '' or savings_num != 'NULL':
        access_checking = True
        send_data('OKOK', 'Commands now pertain to your checking account', clientserv)
    else:
        send_data('ERRO', 'User does not have a checking account', clientserv)
    pass

def SavingsProtocol(data, clientserv, dbserv):
    global access_checking
    global savings_num
    if savings_num != '' or savings_num != 'NULL':
        access_checking = False
        send_data('OKOK', 'Commands now pertain to your savings account', clientserv)
    else:
        send_data('ERRO', 'User does not have a savings account', clientserv)
    pass

def BalanceProtocol(data, clientserv, dbserv):
    global access_checking
    global checking_num
    global savings_num
    if access_checking == True:
        data = checking_num
    else:
        data = savings_num
    send_data('BALC', data, dbserv)
    tipe, response = receive_data(dbserv)
    if tipe == 'OKOK':
        send_data('OKOK', 'Balance for account number ' + data + ': ' + response, clientserv)
    else:
        send_data('ERRO', 'Balance could not be retrieved', clientserv)
    pass 

def TransferProtocol(data, clientserv, dbserv):
    #data should be DestUsername:Amount
    #need to send in format fromAccount:toUsername:Amount
    global access_checking
    global checking_num
    global savings_num
    if access_checking == True: #Withdraw from checking account
        data = checking_num + ':' + data
    else: #withdraw from savings account
        data = savings_num + ':' + data
    
    parts = data.split(':')
    if parts[1].is_valid_usd_amount() == False or len(parts) != 2:
        send_data('ERRO', 'Invalid dollar amount or format', clientserv)

    send_data('SEND', data, dbserv)
    tipe, response = receive_data(dbserv)
    if tipe == 'OKOK':
        send_data('OKOK', 'Transfer successful!', clientserv)
    else:
        send_data('ERRO', 'Could not complete transfer: ', clientserv)
    pass

def DepoWithProtocol(tipe, data, clientserv, dbserv):
    #Message should be formatted as DEPO:50
    #This means that data = 50
    global access_checking
    global checking_num
    global savings_num
    if data.is_valid_usd_amount(): #Must be a positive integer
        if access_checking == True: #checking account
            data = checking_num + ':' + data
        elif access_checking == False: #saving account
            data = savings_num + ':' + data
        else: 
            send_data('ERRO', 'User does not have a savings account', clientserv)
            return
        
        send_data(tipe, data, dbserv)
        tipe, response = receive_data(dbserv)
        if tipe == 'OKOK':
            send_data('OKOK', tipe + ' Successful', clientserv)
        else:
            send_data('ERRO', response, clientserv)
        pass
    else:
        send_data('ERRO', 'Invalid deposit amount', clientserv)  
    pass

    

def mainprotocol(clientserv, dbserv):
    '''
        All threads are run through this function, so the logic needs to be completed by the end of this function.
    '''
    while True:
        comm = DSComm(clientserv)
        mess = comm.recvMessage()
        if mess:
            tipe = mess.getType()
            data = mess.getData().decode('utf-8')
            if ExtractCommand(tipe) == 'Retry':
                send_data('ERRO', 'Must login or sign-up first', clientserv)
                pass
            elif ExtractCommand(tipe) == 'MENU':
                Menu(clientserv)
                pass
            elif ExtractCommand(tipe) == 'LGIN':
                LoginProtocol(data, clientserv, dbserv)
                pass
            elif ExtractCommand(tipe) == 'SIGN':
                SignUpProtocol(data, clientserv, dbserv)
                pass
            elif ExtractCommand(tipe) == 'LGOT':
                LogoutProtocol(data, clientserv, dbserv)
                #Should I break the loop or keep it running?
                pass
            elif ExtractCommand(tipe) == 'OPEN':
                OpenAccountProtocol(data, clientserv, dbserv)
                pass
            elif ExtractCommand(tipe) == 'STAT':
                StatementProtocol(data, clientserv, dbserv)
                pass
            elif ExtractCommand(tipe) == 'CHCK':
                CheckingProtocol(data, clientserv, dbserv)
                pass
            elif ExtractCommand(tipe) == 'SAVI':
                SavingsProtocol(data, clientserv, dbserv)
                pass
            elif ExtractCommand(tipe) == 'BALC':
                BalanceProtocol(data, clientserv, dbserv)
                pass
            elif ExtractCommand(tipe) == 'SEND' or ExtractCommand(tipe, data) == 'RECV':
                TransferProtocol(data, clientserv, dbserv)
                pass
            elif ExtractCommand(tipe) == 'DEPO' or ExtractCommand(tipe) == 'WITH':
                DepoWithProtocol(tipe, data, clientserv, dbserv)
                pass
            else:
                pass
    pass

def threadgenerator(dbserv):
    # Allow for Client Connection
    clientserv = socket.socket()
    # Blank address allows any and all addresses
    clientserv.bind(("", 50000))
    clientserv.listen(5)
    print('Listening on ', str(50000))
    while True:
        clientsock, raddr = clientserv.accept()
        # create a new thread for each connection
        thread = threading.Thread(target=mainprotocol, args=(clientsock, dbserv,))
        thread.start()

    clientserv.close()

if __name__ == '__main__':
    try:
        dbserv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dbserv.connect('localhost', 51000)
        print("Connected to dbserver")
    except:
        print('Unable to Connect to dbserver')
    #Allow for Client Connection
    threadgenerator(dbserv)
    dbserv.close()
