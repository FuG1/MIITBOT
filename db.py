import sqlite3


def init():
    con = sqlite3.connect('db.db')
    cur = con.cursor()
    cur.execute('''CREATE TABLE if not exists ids (id integer unique)''')
    con.commit()


def put_id(ids: int):
    con = sqlite3.connect('db.db')
    cur = con.cursor()
    cur.execute('INSERT OR REPLACE INTO ids (id) VALUES (?)', (ids, ))
    con.commit()


def get_id():
    con = sqlite3.connect('db.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM ids")
    ex = cur.fetchall()
    return ex