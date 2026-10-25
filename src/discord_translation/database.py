import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

def setup_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance INTEGER)''')
    conn.commit()

setup_db()
