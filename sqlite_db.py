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
        # database setup by flask - use:
        #   g.con == connection object
        #   g.cur == cursor


    def first_run(self):
        print('first run')
        con = sqlite3.connect(self.filename)
        cur = con.cursor()
        cur.executescript(open('init.sql').read())
        con.commit()
        con.close()

    def get_user(self, email):
        g.cur.execute("select * from users where email = ?", (email,)) 
        user = g.cur.fetchone()
        if user:
            return user
        return None

    def create_user(self, email, hashed):
        if self.get_user(email):
            return False
        g.cur.execute("insert into users(email, hashed) values(?, ?)", (email, hashed))
        g.con.commit()
        return True

    def update_token(self, email, token, tokendate):
        print(email, token, tokendate)
        g.cur.execute("update users set token = ?, tokendate = ? where email = ?", (token, tokendate, email))
        g.con.commit()

    def get_note(self, email, key, version=None):
        user = self.get_user(email)
        g.cur.execute("select id, key, deleted, modifydate, createdate, syncnum, version, minversion, sharekey, publishkey, content, pinned, markdown, unread, list from notes where key = ? and userid = ?", (key, user['id']))
        note = g.cur.fetchone()
        # TODO: +future +enhancement check for share key to allow sharing notes around users
        if note and version:
            # TODO: implement
            self.cur.execute("select content from versions where key = ? and version = ?", (key, version))
            old_content = self.cur.fetchone()
            note['content'] = old_content['content']

        tagsOBJ = g.cur.execute("select name from tagged join tags on id=tagid where noteid=?", (note['id'],)).fetchall()
        if tagsOBJ:
            note['tags'] = [x['name'] for x in tagsOBJ]
        else:
            note['tags'] = []


        systemtags = [tag for tag in ['pinned', 'markdown', 'unread', 'list'] if note.get(tag, None)]
        note['systemtags'] = systemtags
        # TODO: remove markdown, list, etc. keys from note dict (they should only be in systemtags)

        del note['id']
        return note


    def create_note(self, email, note_data):
        user = self.get_user(email)

        note_data['userid'] = user['id']

        sys_tags = note_data['systemtags']
        for t in ['pinned', 'markdown', 'list']:
            note_data[t] = 1 if t in sys_tags else 0

        g.cur.execute('insert into notes(userid, key, deleted, modifydate, createdate, syncnum, version, minversion, content, pinned, markdown, list)   values (:userid, :key, :deleted, :modifydate, :createdate, :syncnum, :version, :minversion, :content, :pinned, :markdown, :list)', note_data)

        row_id = g.cur.execute('select id from notes where key=?', (note_data['key'],)).fetchone()['id']

        for t in note_data['tags']:
            i = self.get_and_create_tag(t)
            self.tagit(key, i)
        
        g.con.commit()
        return True

    def tagit(self, notekey, tag):
        noteid = g.cur.execute('select id from notes where key = ?', (key,)).fetchone()['id']
        g.cur.execute('insert into tagged select ?, ? where not exists (select * from tagged where noteid = ? and tagid = ?', (noteid, tag, noteid, tag))


    def get_and_create_tag(self, t):
        if not g.cur.execute('select * from tags where lower_name = ?', (t.lower(),)).fetchone():
            g.cur.execute('insert into tags(_index, name, lower_name, version) values (?, ?, ?, ?)', (1, t, t.lower(), 1))
        return g.cur.execute('select id from tags where lower_name = ?', (t.lower(),)).fetchone()['id']



    # TODO: don't forget index is stored in sql as _index

    def update_note(self, key, data):
        # TODO: this broken
        self.cur.execute("update notes set deleted=:deleted, modifydate=:modifydate, syncnum=:syncnum, minversion=:minversion, publishkey=:publishkey, content=:content  where key = ?", key, **data)
        self.con.commit()
        #TODO: handle tags (here or higher up?)

