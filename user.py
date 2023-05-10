#!/usr/bin/python3
import hashlib
import uuid
import random
import datetime

from db import Database
class user:
    def __init__(self, ):
        self.db = Database() 
        
    def login(self, username, password) -> str: #on successful login, returns userID from DB
        result = self.db.execute_query('SELECT userID FROM users WHERE username = %s AND password = %s', (username, hash(password)))
        if len(result) > 0:
            #User found, return UserID
            print("User found, returning UserID")
            return result[0]['userID']
        else:
            #User not found
            print("User not found")
            return -1 #User not found, return -1
        
    def create_user(self, username, password, name, address, phone_num):
        new_user = {
        'username': username,
        'password': hash(password),
        'name': name,
        'address': address,
        'phone_num': phone_num
     }
        new_user['userID'] = str(uuid.uuid4())
        
        try:
            self.db.add_row_to_table('users', new_user)
            return new_user['userID']
        except:
            print("Could not add user")
            return -1
            
    def create_account(self, userID, type):
        if type == 'CHCK':
            type = 'checkings'
        else:
            type = 'savings'
        new_user = {
            'userID': userID,
            'type': type, 
            'balance': 0
        }
        new_user['account_num'] = str(unique_digits(10))

        try:
            self.db.add_row_to_table('account', new_user)
            print("Successfully added account")
            return new_user['account_num']
        except:
            print("Could not add account")
    
    def list_account(self, userID):
        result = self.db.execute_query('select account_num, type from account where userID = %s ', (userID))
        
        if len(result) > 0:
            
            #Account found
            print("User found, returning available accounts")
            print(result)
            return result #[{'account_num': '6370429581', 'type': 'savings'}, {'account_num': '9643572018', 'type': 'checkings'}]
        else:
            #Account not found
            print("User does not exist")
            return -1 #User not found, return -1
    
    def deposit(self, account_num, val):
        try: 
            result = self.db.execute_query('update account set balance = balance + %s where account_num = %s', (val, account_num))
            print(f"Sussfully deposited {val} into Account: {account_num}")
            return 1
        except:
            print("Could not complete deposit")
            return -1

    def withdraw(self, account_num,val):
        if not self.check_funds(account_num, val):
            print("Withdrawal failed: Insufficient funds")
            return
        try: 
            result = self.db.execute_query('update account set balance = balance - %s where account_num = %s', (val, account_num))
            print(f"Successfully withdrew {val} from Account: {account_num}")
            return 1
        except:
            print("Could not complete withdrawal")
            return -1
    
    def get_balance(self, account_num)->float:
        try: 
            result = self.db.execute_query('select balance from account where account_num = %s', (account_num))
            balance = float(result[0]['balance'])
            print(balance)
            return balance
        except:
            return -1 #could not get balance
    
    def transfer(self, account_num, username, val):
        if not self.check_funds(account_num, val):
            print("Transfer failed: Insufficient funds")
            return -1
        try: 
            result = self.db.execute_query("SELECT account_num from account where type = 'checkings' AND  userID = (SELECT userID from users where username = %s)",(username))
            reciever_account_num = result[0]['account_num']
        except: 
            print(f"Could not find account number for: {username}")
        
        sender = {
            'account_num': account_num,
            'direction': 'out',
            'amount': val,
            'other_account': reciever_account_num
        }
        sender['transferID'] = str(unique_digits(10))
        
        reciever = {
            'account_num': reciever_account_num,
            'direction': 'in',
            'amount': val,
            'other_account': account_num
        }
        reciever['transferID'] = str(unique_digits(10))

        try:
            self.withdraw(account_num, val)
            self.deposit(reciever_account_num, val)
            self.db.add_row_to_table('transfer', sender)
            self.db.add_row_to_table('transfer', reciever)
            print("Transfer Success") 
            return 1
        except:
            print("Transfer Failure")
            return -1
        
   
    def check_funds(self, account_num, val)->bool:
        current_balance = self.get_balance(account_num)  # retrieve the current balance of the account
        if current_balance - float(val) < 0:
            return False #insufficient balance
        else:
            return True
    
    def check_statement(self,account_num, day):
        try:
            result_in = self.db.execute_query("SELECT * FROM transfer WHERE date BETWEEN CURDATE() - INTERVAL %s DAY AND CURDATE() + INTERVAL 1 DAY  AND account_num = %s AND direction = 'in';",(day, account_num))
            result_out = self.db.execute_query("SELECT * FROM transfer WHERE date BETWEEN CURDATE() - INTERVAL %s DAY AND CURDATE() + INTERVAL 1 DAY  AND account_num = %s AND direction = 'out';",(day, account_num))
            return self.formatStatement(account_num, day, result_in, result_out)
            
        except:
            print("Could not retrieve statement")
            return -1
    
    def getUsername(self, account_num):
        try:
            result = self.db.execute_query("select username from users where userId = (select userID from account where account_num = %s)",(account_num))
            return(result[0]['username'])
        except:
            print("Could not retrieve username")
            return -1
        
    def getType(self, account_num):
        try:
            result = self.db.execute_query("select type from account where account_num = %s",(account_num))
            return(result[0]['type'])
        except:
            print("Could not retrieve type")
            return -1
    def formatStatement(self, account_num, day, result_in, result_out):
        total_in = 0
        total_out = 0
        output = "-----------------------------------------------------------\n"
        output += f'{getDay(day)} statement for {self.getUsername(account_num)}\'s {self.getType(account_num)} account:\n\nReceived:\n'
        output += f"{'Amount':<20}{'From':<20}{'Date'}\n"
        for x in result_in:
            amt = x['amount']
            other = self.getUsername(x['other_account'])
            date = x['date']
            total_in +=amt
            output += f"${amt:<19}{other:<20}{date}\n"

        output += "\nSent:\n"
        output += f"{'Amount':<20}{'To':<20}{'Date'}\n"
        for x in result_out:
            amt = x['amount']
            other = self.getUsername(x['other_account'])
            date = x['date']
            total_out += amt
            output += f"${amt:<19}{other:<20}{date}\n"

        output += f"\nYou received ${total_in} and sent ${total_out} this statement\n"
        output += "-----------------------------------------------------------\n"
        return output


def hash(str)->str:
    hash_obj = hashlib.sha1()
    hash_obj.update(str.encode('utf8'))
    hex = hash_obj.hexdigest()
    return hex

def unique_digits(x)->str: #x represents the number of unique digits
    digits = random.sample(range(x), x)
    return ''.join(map(str, digits))

def getDay(day):
    if day == '0':
        str_day = "Daily"
    elif day == '7':
        str_day = "Weekly"
    elif day == '30':
        str_day = "Monthly"
    else:
        str_day = None
    return str_day





