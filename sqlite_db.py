# low level db access - does no error checking or validation
# provides abstraction between the actual database (sqlite, mongo, etc) and the db_frontend.py

import sqlite3
import os.path
import datetime
import re

from db import DB
from flask import g

RE_int = re.compile(r'\d+') # re to check if string is positive integer (no + prefix allowed)


class Database(DB):
    def __init__(self, args):
        super(Database, self).__init__(args)
        self.filename = args['FILE']
        self.init_file = args['INIT_SQL_FILE']
        # database setup by flask - use:
        #   g.con == connection object
        #   g.cur == cursor

    def first_run(self):
        con = sqlite3.connect(self.filename)
        cur = con.cursor()
        init_sql_file = open(self.init_file)
        cur.executescript(init_sql_file.read())
        init_sql_file.close()
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
        g.cur.execute("update users set token = ?, tokendate = ? where email = ?", (token, tokendate, email))
        g.con.commit()

    def get_note(self, email, key, version=None):
        user = self.get_user(email)

        # 'and userid =' is to ensure note is owned by user
        g.cur.execute("select key, deleted, modifydate, createdate, syncnum, version, minversion, sharekey, publishkey, content, pinned, markdown, unread, list from notes where key = ? and userid = ?", (key, user['id']))
        note = g.cur.fetchone()
        if not note:
            return None
        # TODO: +future +enhancement check for share key to allow sharing notes around users

        # below also means getting latest version will return full note
        if note and version and version != note['version']:
            g.cur.execute("select * from versions where key = ? and version = ?", (key, version))
            note = g.cur.fetchone()
            return note

        tagsOBJ = g.cur.execute("select name from tagged join tags on id=tagid where notekey=?", (key,)).fetchall()
        if tagsOBJ:
            note['tags'] = [x['name'] for x in tagsOBJ]
        else:
            note['tags'] = []


        systemtags = [tag for tag in ['pinned', 'markdown', 'unread', 'list'] if note.get(tag, None)]
        note['systemtags'] = systemtags

        # remove unnecessary keys
        del note['pinned']
        del note['markdown']
        del note['unread']
        del note['list']

        return note


    def create_note(self, email, note_data):
        user = self.get_user(email)

        note_data['userid'] = user['id']

        sys_tags = note_data['systemtags']
        for t in ['pinned', 'markdown', 'list']:
            note_data[t] = 1 if t in sys_tags else 0

        g.cur.execute('insert into notes(userid, key, deleted, modifydate, createdate, syncnum, version, minversion, content, pinned, markdown, list)   values (:userid, :key, :deleted, :modifydate, :createdate, :syncnum, :version, :minversion, :content, :pinned, :markdown, :list)', note_data)

        key = note_data['key']
        for t in note_data['tags']:
            i = self.get_and_create_tag(t)
            self.tagit(key, i)

        g.con.commit()
        return True

    def tagit(self, notekey, tag):
        g.cur.execute('insert into tagged select ?, ? where not exists (select * from tagged where notekey = ? and tagid = ?)', (notekey, tag, notekey, tag))


    def get_and_create_tag(self, t):
        if not g.cur.execute('select * from tags where lower_name = ?', (t.lower(),)).fetchone():
            g.cur.execute('insert into tags(_index, name, lower_name, version) values (?, ?, ?, ?)', (1, t, t.lower(), 1))
            g.con.commit()
        return g.cur.execute('select id from tags where lower_name = ?', (t.lower(),)).fetchone()['id']



    # TODO: don't forget index for tag is stored in sql as _index


    def update_note(self, email, note_data):
        # note - note_data contains key
        user = self.get_user(email)

        note_data['userid'] = user['id']

        sys_tags = note_data['systemtags']
        for t in ['pinned', 'markdown', 'list']:
            note_data[t] = 1 if t in sys_tags else 0

        g.cur.execute("update notes set deleted=:deleted, modifydate=:modifydate, createdate=:createdate, syncnum=:syncnum, minversion=:minversion, publishkey=:publishkey, content=:content, version=:version, pinned=:pinned, markdown=:markdown, list=:list where key = :key and userid = :userid", note_data)

        key = note_data['key']
        for t in note_data['tags']:
            i = self.get_and_create_tag(t)
            self.tagit(key, i)

        g.con.commit()
        return True


    def delete_note(self, email, key):
        # check user owns note
        # delete all tagged entries associated
        # delete all versions with same key
        # delete note by key

        user = self.get_user(email)

        # 'and userid =' is to ensure note is owned by user
        g.cur.execute("select * from notes where key = ? and userid = ?", (key, user['id']))
        note = g.cur.fetchone()
        if not note:
            return ("note not found", 404)
        elif note['deleted'] == 0:
            return ("must send note to trash before permanently deleting", 400)

        g.cur.execute("delete from tagged where notekey = ?", (key,))

        # TODO: delete all tags that no longer have a tagged entry

        g.cur.execute("delete from versions where key = ?", (key,))

        g.cur.execute("delete from notes where key = ?", (key,))

        g.con.commit()

        return ("", 200)



    def save_version(self, email, notekey):
        user = self.get_user(email)

        g.cur.execute('insert into versions select key, modifydate, content, version from notes where key = ? and userid = ?', (notekey, user['id']))
        g.con.commit()

    def drop_old_versions(self, email, notekey, minversion):
        print(g.cur.execute('select * from versions').fetchall())
        g.cur.execute('delete from versions where version < ? and key = ?', (minversion, notekey))
        g.con.commit()


    def notes_index(self, username, length, since, mark):
        user = self.get_user(username)

        # set defaults for mark (currently length and since must be valid)
        if not mark:
            mark = "0"
        if RE_int.match(mark):
            mark = int(mark)
        else:
            return ("invalid mark parameter", 400)

        if length < 1:
            return ("length must be greater than 0", 400)
            # return { "count": 0, "data": []} # ha caught you there
        # should throw error if length too large? (nah, let's be nice)
        length = min(length, 100)


        g.cur.execute("select rowid, key, deleted, modifydate, createdate, syncnum, version, minversion, sharekey, publishkey, pinned, markdown, unread, list from notes where userid = ? and rowid > ? and modifydate > ? order by rowid", (user['id'], mark, since))
        notes = g.cur.fetchall()

        newmark = None
        if len(notes) > length:
            newmark = notes[length-1]['rowid']
            notes = notes[:length]


        # ok there's probably a more efficient way to process notes here....
        # contributes of code or ideas welcome ;)
        for note in notes:
            key = note['key']
            tagsOBJ = g.cur.execute("select name from tagged join tags on id=tagid where notekey=?", (key,)).fetchall()
            if tagsOBJ:
                note['tags'] = [x['name'] for x in tagsOBJ]
            else:
                note['tags'] = []


            systemtags = [tag for tag in ['pinned', 'markdown', 'unread', 'list'] if note.get(tag, None)]
            note['systemtags'] = systemtags
            del note['rowid']
            del note['pinned']
            del note['markdown']
            del note['unread']
            del note['list']

        data = {}
        data['count'] = len(notes)
        data['data'] = notes
        if newmark:
            data['mark'] = newmark

        return (data, 200)








