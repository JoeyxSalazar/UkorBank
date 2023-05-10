#!/usr/bin/python3
from user import user
from DSComm import DSComm
from DSMessage import DSMessage
import socket
import threading

db = user()
def send_data(type, data, sock):
    mess = DSMessage()
    mess.setType(type)
    if isinstance(data, bytes) == False:
        mess.setData(data.encode('utf-8'))
    else:
        mess.setData(data)
    comm = DSComm(sock)
    comm.sendMessage(mess)
#Create New User
def createAccountProtocol(id, type):
    db.create_account(id, type)

def createUserProtocol(type, username, password, name, email, phone_num):
    id = db.create_user("testest1", "password", "Joey Salazar", "home", "305")
    if id == -1:
        return -1
    createAccountProtocol(id, type)
    return 1

    
#Login
def loginProtocol(username, password):
    id = db.login(username, password)
    accounts = db.list_account(id)
    
    check = "NULL"
    savings = "NULL"
    for account in accounts:
        if account['type'] == "checkings":
            check = account['account_num']
        if account['type'] == "savings":
            savings = account['account_num']
    result = id+":"+check+":"+savings
    return result

#Transfer
def transferProtocol(account_num, username, val):
    return db.transfer(account_num, username, val)

#Get Balance
def balanceProtocol(account_num)->float:
    return db.get_balance(account_num)

#Get Statement
def statementProtocol(account_num, day):
    return db.check_statement(account_num, day)

#Withdraw
def withdrawProtocol(account_num, val):
    return db.withdraw(account_num, val)
    
#Deposit
def depositProtocol(account_num, val):
    return db.deposit(account_num, val)



#These all need to send something to the middleware or will become stuck in loop
def decode_cmd(cmd, data, midsock):
    creds = data.split(':')
    if cmd == 'LGIN':
        #username:password
        status = loginProtocol(creds[0], creds[1]) 
        if status != -1:
            send_data('OKOK', status, midsock)
        else:
            send_data('ERRO', 'Could not find user', midsock)
    elif cmd == 'SIGN':
        #tipe:username:password:name:email:phone_num
        status = createUserProtocol(creds[0], creds[1], creds[2], creds[3], creds[4], creds[5])
        if status == 1:
            send_data('OKOK', 'Sign up complete, Try logging in now', midsock)
        else:
            send_data('ERRO', 'Error Signing Up', midsock)
    elif cmd == 'OPEN':
        #user_id:type
        createAccountProtocol(creds[0], creds[1])
        send_data('OKOK', 'Account Created', midsock)
    elif cmd == 'STAT':
        #unsure still
        statementProtocol()
        send_data('ERRO', 'No protocol in place for statements right now', midsock)
    elif cmd == 'BALC':
        #chck/savi_num
        amount = balanceProtocol(creds[0])
        if amount != -1:
            send_data('OKOK', amount, midsock)
        else:
            send_data('ERRO', 'Error retrieving balance', midsock)
    elif cmd == 'SEND':
        #fromAccount:toUsername:amount
        status = transferProtocol(creds[0], creds[1], creds[2])
        if status == 1:
            send_data('OKOK', 'Transfer Success!', midsock)
        else:
            send_data('ERRO', 'Error making transfer', midsock)
    elif cmd == 'DEPO':
        #accountnum:amount
        status = depositProtocol(creds[0], creds[1])
        if status == 1:
            send_data('OKOK', 'Transfer Success!', midsock)
        else:
            send_data('ERRO', 'Error making transfer', midsock)
    elif cmd == 'WITH':
        #accountnum:amount
        status = withdrawProtocol(creds[0], creds[1])
        if status == 1:
            send_data('OKOK', 'Transfer Success!', midsock)
        else:
            send_data('ERRO', 'Error making transfer', midsock)
    else:
        send_data('ERRO', 'Invalid Command', midsock)

def db_protocol(middlesock):
    comm = DSComm(middlesock)
    print('DB Protocol')
    while True:
        print('\tListening for message')
        mess = comm.recvMessage()
        if mess:
            tipe = mess.getType()
            data = mess.getData().decode('utf-8')
            print('Command:', tipe, '\t', 'Data: ', data)  
            decode_cmd(tipe, data, middlesock)

if __name__ == "__main__":
    '''Assume TCP Connections'''
    middleserv = socket.socket()
    middleserv.bind(("localhost", 51000))
    middleserv.listen(5)
    while True:
        print('Listening on ' + '51000')
        middlesock, raddr = middleserv.accept()
        db_protocol(middlesock)
        middlesock.close()
    middleserv.close()

