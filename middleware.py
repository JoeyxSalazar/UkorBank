import socket
import time
import threading
import subprocess
import re
from DSMessage import DSMessage
from DSComm import DSComm

class Program:
    def __init__(self):
        self.logged_in = False
        self.access_checking = True
        self.user_id = ""
        self.checking_num = ""
        self.savings_num = ""

    def handle_client(self, clientsock, dbsock):
        mainprotocol(self, clientsock, dbsock)
        pass

def is_valid_usd_amount(s):
    pattern = re.compile(r'^\d+(\.\d{2})?$')
    if pattern.match(s):
        return True
    return False

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
def ExtractCommand(clientinstance, tipe):
    if clientinstance.logged_in == True or tipe == 'LGIN' or tipe == 'SIGN':
        return tipe
    else:
        return 'Retry'
    
def LoginProtocol(clientinstance, data, clientserv, dbserv):
    #data should be formatted as username:password
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
                clientinstance.logged_in = True
                creds = user_data.split(':')
                if len(creds) == 3:
                    clientinstance.user_id, clientinstance.checking_num, clientinstance.savings_num = creds[0], creds[1], creds[2]
                    send_data('OKOK', 'Login Success!', clientserv)
                else:
                    send_data('ERRO', 'Error retrieving credentials', clientserv)
                    clientinstance.logged_in = False
                    return
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
    if len(creds) != 6:
        send_data('ERRO', 'Invalid sign-up format', clientserv)
    else:
        send_data('SIGN', data, dbserv)
        tipe, response = receive_data(dbserv)
        if tipe == 'OKOK':
            send_data('OKOK', 'Account Created!', clientserv)
        else:
            send_data('ERRO', 'Error creating your account.', clientserv)
    pass

def OpenAccountProtocol(clientinstance, data, clientserv, dbserv):
    #data should be type
    if data != 'CHCK' and data != 'SAVI':
        send_data('ERRO', 'Invalid Account Type', clientserv)
    elif data == 'CHCK' and (clientinstance.checking_num == '' or clientinstance.checking_num == 'NULL'):
        data = clientinstance.user_id + ':' + data
        send_data('OPEN', data, dbserv)
        tipe, response = receive_data(dbserv)
        if tipe == 'OKOK':
            clientinstance.checking_num = response
            send_data('OKOK', 'Account Created!', clientserv)
        else:
            send_data('ERRO', 'Error creating account', clientserv)
        pass
    elif data == 'SAVI' and (clientinstance.savings_num == '' or clientinstance.savings_num == 'NULL'):
        data = clientinstance.user_id + ':' + data
        send_data('OPEN', data, dbserv)
        tipe, response = receive_data(dbserv)
        if tipe == 'OKOK':
            clientinstance.savings_num = response
            send_data('OKOK', 'Account Created!', clientserv)
        else:
            send_data('ERRO', 'Error creating account', clientserv)
        pass
    else:
        send_data('ERRO', 'Account already exists! Otherwise, unknown error', clientserv)  
    pass


def LogoutProtocol(clientinstance, data, clientserv, dbserv):
    clientinstance.logged_in = False
    clientinstance.user_id = ""
    clientinstance.checking_num = ""
    clientinstance.savings_num = ""
    send_data('OKOK', 'Logout Success!', clientserv)
    pass

def AccountProtocol(clientinstance, data, clientserv, dbserv):
    Account_Details = "Checkings Account Number: " + clientinstance.checking_num + '\nSavings Account Number: ' + clientinstance.savings_num
    send_data('OKOK', Account_Details, clientserv)
    pass

def StatementProtocol(clientinstance, data, clientserv, dbserv):
    #data = 0/7/30
    if data != str(0) and data != str(7) and data != str(30): 
        send_data('ERRO', 'Invalid statement type', clientserv)
    else:
        if clientinstance.access_checking == True:
            data = clientinstance.checking_num + ':' + data
        else:
            data = clientinstance.savings_num + ':' + data
        send_data('STAT', data, dbserv)
        tipe, response = receive_data(dbserv)
        if tipe == 'OKOK':
            send_data('OKOK', response, clientserv)
        else:
            send_data('ERRO', 'Couldnt retrieve statement', clientserv)
    pass

def CheckingProtocol(clientinstance, data, clientserv, dbserv):
    if clientinstance.checking_num != '' or clientinstance.checking_num != 'NULL':
        clientinstance.access_checking = True
        send_data('OKOK', 'Commands now pertain to your checking account', clientserv)
    else:
        send_data('ERRO', 'User does not have a checking account', clientserv)
    pass

def SavingsProtocol(clientinstance, data, clientserv, dbserv):
    if clientinstance.savings_num != '' or clientinstance.savings_num != 'NULL':
        clientinstance.access_checking = False
        send_data('OKOK', 'Commands now pertain to your savings account', clientserv)
    else:
        send_data('ERRO', 'User does not have a savings account', clientserv)
    pass

def BalanceProtocol(clientinstance, data, clientserv, dbserv):
    if clientinstance.access_checking == True:
        data = clientinstance.checking_num
    else:
        data = clientinstance.savings_num
    send_data('BALC', data, dbserv)
    tipe, response = receive_data(dbserv)
    if tipe == 'OKOK':
        send_data('OKOK', 'Balance for account number ' + str(data) + ': ' + str(response), clientserv)
    else:
        send_data('ERRO', 'Balance could not be retrieved', clientserv)
    pass 

def TransferProtocol(clientinstance, data, clientserv, dbserv):
    #data should be DestUsername:Amount
    #need to send in format fromAccount:toUsername:Amount
    if clientinstance.access_checking == True: #Withdraw from checking account
        data = clientinstance.checking_num + ':' + data
    else: #withdraw from savings account
        data = clientinstance.savings_num + ':' + data

    """parts = data.split(':')
    if not(parts[1].isdigit()):
        if is_valid_usd_amount(parts[1]) == False or len(parts) != 2:
            send_data('ERRO', 'Invalid dollar amount or format', clientserv)"""

    send_data('SEND', data, dbserv)
    tipe, response = receive_data(dbserv)
    if tipe == 'OKOK':
        send_data('OKOK', 'Transfer successful!', clientserv)
    else:
        send_data('ERRO', 'Could not complete transfer: ', clientserv)
    pass

def DepoWithProtocol(clientinstance, tipe, data, clientserv, dbserv):
    #Message should be formatted as DEPO:50
    #This means that data = 50
    if is_valid_usd_amount(data): #Must be a positive integer
        if clientinstance.access_checking == True: #checking account
            data = clientinstance.checking_num + ':' + data
        elif clientinstance.access_checking == False: #saving account
            data = clientinstance.savings_num + ':' + data
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

    

def mainprotocol(clientinstance, clientserv, dbserv):
    '''
        All threads are run through this function, so the logic needs to be completed by the end of this function.
    '''
    Menu(clientserv)
    while True:
        comm = DSComm(clientserv)
        mess = comm.recvMessage()
        if mess:
            tipe = mess.getType()
            data = mess.getData().decode('utf-8')
            print(data)
            if ExtractCommand(clientinstance, tipe) == 'Retry':
                send_data('ERRO', 'Must login or sign-up first', clientserv)
                pass
            elif ExtractCommand(clientinstance, tipe) == 'MENU':
                Menu(clientserv)
                pass
            elif ExtractCommand(clientinstance, tipe) == 'LGIN':
                LoginProtocol(clientinstance, data, clientserv, dbserv)
                pass
            elif ExtractCommand(clientinstance, tipe) == 'SIGN':
                SignUpProtocol(data, clientserv, dbserv)
                pass
            elif ExtractCommand(clientinstance, tipe) == 'LGOT':
                LogoutProtocol(clientinstance, data, clientserv, dbserv)
                #Should I break the loop or keep it running?
                pass
            elif ExtractCommand(clientinstance, tipe) == 'ACCT':
                AccountProtocol(clientinstance, data, clientserv, dbserv)
                pass
            elif ExtractCommand(clientinstance, tipe) == 'OPEN':
                OpenAccountProtocol(clientinstance, data, clientserv, dbserv)
                pass
            elif ExtractCommand(clientinstance, tipe) == 'STAT':
                StatementProtocol(clientinstance, data, clientserv, dbserv)
                pass
            elif ExtractCommand(clientinstance, tipe) == 'CHCK':
                CheckingProtocol(clientinstance, data, clientserv, dbserv)
                pass
            elif ExtractCommand(clientinstance, tipe) == 'SAVI':
                SavingsProtocol(clientinstance, data, clientserv, dbserv)
                pass
            elif ExtractCommand(clientinstance, tipe) == 'BALC':
                BalanceProtocol(clientinstance, data, clientserv, dbserv)
                pass
            elif ExtractCommand(clientinstance, tipe) == 'SEND' or ExtractCommand(clientinstance, tipe) == 'RECV':
                TransferProtocol(clientinstance, data, clientserv, dbserv)
                pass
            elif ExtractCommand(clientinstance, tipe) == 'DEPO' or ExtractCommand(clientinstance, tipe) == 'WITH':
                DepoWithProtocol(clientinstance, tipe, data, clientserv, dbserv)
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
        # create a new instance of the Program class for this client
        program = Program()
        # create a new thread for each connection
        thread = threading.Thread(target=program.handle_client, args=(clientsock, dbserv,))
        thread.start()

    clientserv.close()

if __name__ == '__main__':
    try:
        dbserv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dbserv.connect(('localhost', 51000))
        print("Connected to dbserver")
    except:
        print('Unable to Connect to dbserver')
    #Allow for Client Connection
    threadgenerator(dbserv)
    dbserv.close()

#I added this
