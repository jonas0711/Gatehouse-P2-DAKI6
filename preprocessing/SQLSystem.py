import sqlite3 as sql
from sqlite3 import Error

#To connect to the database file
def create_connection(path):
    connection = None
    try:
        connection = sql.connect(path)
        print("Connection to SQLite DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

#To run SQL commands
def execute_query(connection, query, params = None):
    cursor = connection.cursor()
    try:
        if params:
            cursor.executemany(query, params)
        else:
            cursor.execute(query)
        connection.commit()
        #print("Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

#To read data from the database
def fetch_query(connection, query):
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchone()  # Fetch one record
    return result