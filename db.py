#username: admin
#pass: Zr838083
#host: venmodb.cibfdscxonjj.us-east-2.rds.amazonaws.com
#port: 3306

import pymysql
import uuid

from pymysql.constants import CLIENT

class Database:


    database_cred = {

        "host": "database-1.cibfdscxonjj.us-east-2.rds.amazonaws.com",

        "user": "admin",

        "password": "",

        "database": "database",

        "autocommit": True,  # making sure updated, inserts, deletions are commited for every query

        "cursorclass": pymysql.cursors.DictCursor,

    }


    def __init__(self, database_cred: dict = None):

        if database_cred:

            self.conn = pymysql.connect(**database_cred)

        else:

            self.conn = pymysql.connect(**self.database_cred)

        # end if


    def add_row_to_table(self, table_name, row_values):
        # Create a cursor object to execute SQL queries
        cursor = self.conn.cursor()
        
        # Build the INSERT statement
        columns = ', '.join(row_values.keys())
        values = ', '.join(['%s']*len(row_values))
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
        
        # Execute the query with the provided row values
        cursor.execute(sql, tuple(row_values.values()))
        
        # Commit the changes to the database
        self.conn.commit()
    
    def execute_query(self, query, args=()):
        cursor = self.conn.cursor()
        cursor.execute(query, args)
        result = cursor.fetchall()
        return result
