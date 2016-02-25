# low level db access - does no error checking or validation
# provides abstraction between the actual database (sqlite, mongo, etc) and the db_frontend.py

import sqlite3
import os.path
import datetime

class DB(object):
    def __init__(self, args):
        pass

    def get_user(self, email):
        """ should return a dictionary containing email/username, hashed password, token, token expiry date, id """
        raise NotImplemented()

    def create_user(self, email, hashed):
        raise NotImplemented()

    def update_token(self, email, token, tokendate):
        raise NotImplemented()

    def get_note(self, key, version=None):
        raise NotImplemented()

    def update_note(self, key, data):
        raise NotImplemented()

from flask import g

class Database(DB):
    def __init__(self, args):
        super(Database, self).__init__(args)

        self.filename = args['FILE']
        self.con = sqlite3.connect(self.filename)
        self.con.row_factory = sqlite3.Row # so returns dictionary of stuff, rather than tuples
        self.cur = self.con.cursor()

    def first_run(self):
        self.cur.executescript(open('init.sql').read())
        self.con.commit()

    def get_user(self, email):
        print(email)
        cur = g.db.cursor()
        cur.execute("select * from users where email = ?", (email,)) 
        user = cur.fetchone()
        print(user)
        return user

    def create_user(self, email, hashed):
        print('creating user!')
        if self.get_user(email):
            return False
        g.db.cursor().execute("insert into users(email, hashed) values(?, ?)", (email, hashed))
        g.db.commit()
        print(g.db.cursor().execute('select * from users').fetchall())
        return True

    def update_token(self, email, token, tokendate):
        self.cur.execute("update users set token = ?, tokendate = ? where email = ?", token, tokendate, token)
        self.con.commit()

    def get_note(self, key, version=None):
        self.cur.execute("select * from notes where key = ?", key)
        note =  self.cur.fetchone()
        if note and version:
            self.cur.execute("select content from versions where key = ? and version = ?", key, version)
            old_content = self.cur.fetchone()
            note['content'] = old_content['content']
        return note


    def update_note(self, key, data):
        self.cur.execute("update notes set deleted=:deleted, modifydate=:modifydate, syncnum=:syncnum, minversion=:minversion, publishkey=:publishkey, content=:content  where key = ?", key, **data)
        self.con.commit()
        #TODO: handle tags (here or higher up?)

