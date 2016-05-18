
# high level db access
# must define lowerlevel db something...

import datetime
import uuid
import copy
import re

class Database():
    def __init__(self, thedatabase):
        self.database = thedatabase

    def get_user(self, username):
        userdata = self.database.get_user(username)
        if not userdata:
            return None
        if userdata.get('token', None):
            # remove if over 24 hours old
            if (datetime.datetime.utcnow().timestamp() - userdata['tokendate']) > 86400:
                userdata['token'] = None
        else:
            userdata['token'] = None
        return userdata

    def create_user(self, username, hashed):
        result =  self.database.create_user(username, hashed)
        return result

    def check_token(self, username, token):
        user = self.get_user(username)
        if user and user.get('token') and user['token'] == token:
            return True
        return False

    def get_token(self, username):
        user = self.get_user(username)

        # if already token, return it
        if user['token']:
            return user['token']

        # otherwise generate a new one
        token = (str(uuid.uuid4())+str(uuid.uuid4())).replace('-','').upper()
        tokendate = datetime.datetime.utcnow().timestamp()
        self.database.update_token(user['email'], token, tokendate)
        return token

    def get_note(self, username, notekey, version=None):
        note = self.database.get_note(username, notekey, version)
        if not note:
            return None
        return note

    def update_note(self, username, notekey, data):
        # TODO: check/validate data types

        # TODO: use syncnum to resolve conflicts (if syncnum in new data is lower, don't use)
        old_note = self.get_note(username, notekey)
        if not old_note:
            return ('note with that key does not exist', 404)

        content =  data.get('content', None)
        if content and content != old_note['content']:
            # then save old version
            self.database.save_version(username, notekey)
            old_note['content'] = content
            # TODO: currently version only increments when content changes (is this wanted?) - either way, syncnum is inc'd
            old_note['version'] += 1

        s = datetime.datetime.utcnow().timestamp()

        old_note['modifydate'] = min(s, data.get('modifydate', s))
        # old_note['createdate'] = min(s, data.get('createdate', s)) # TODO: should createdate ever be modified?

        # TODO: handle version in new note data (ie for merge? and _whether to update or not_ - don't overwrite newer note with older note)

        old_note['minversion'] = max(old_note['version'] - 20, 1)  #TODO: allow configuring number of versions to keep

        self.database.drop_old_versions(username, notekey, old_note['minversion'])

        # TODO: handling sharekey?

        deleted = data.get('deleted', None)
        if deleted == '1' or deleted == '0':
            deleted = int(deleted)
        if (deleted in [1,0]):
            old_note['deleted'] = deleted

        if 'systemtags' in data:
            old_note['systemtags'] = [t for t in set(data.get('systemtags',[])) if t in ('pinned', 'markdown', 'list')]

        if 'tags' in data:
            tags = []
            for t in set(data.get('tags', [])):
                safe_tag = self._validate_tag(t)
                if safe_tag:
                    tags.append(safe_tag)
            old_note['tags'] = tags


        old_note['syncnum'] += 1

        ok = self.database.update_note(username, copy.deepcopy(old_note))
        if ok:
            return (old_note, 200)
        return ('unable to create note', 400)

    def create_note(self, username, data):
        note_data = {}
        if 'content' not in data:
            return ('note must contain a content field', False)
        note_data['content'] = str(data['content'])

        note_data['key'] = str(uuid.uuid4()) + str(int(datetime.datetime.utcnow().timestamp()))

        s = datetime.datetime.utcnow().timestamp()
        note_data['modifydate'] = min(s, data.get('modifydate', s))
        note_data['createdate'] = min(s, data.get('createdate', s))

        note_data['version'] = 1
        note_data['minversion'] = 1
        note_data['publishkey'] = None
        note_data['syncnum'] = 1

        deleted = data.get('deleted', 0)
        if deleted == '1' or deleted == '0':
            deleted = int(deleted)
        elif deleted != 1:
            deleted = 0

        note_data['deleted'] = deleted

        note_data['systemtags'] = [t for t in set(data.get('systemtags',[])) if t in ('pinned', 'markdown', 'list')]

        tags = []
        for t in set(data.get('tags', [])):
            safe_tag = self._validate_tag(t)
            if safe_tag:
                tags.append(safe_tag)
        note_data['tags'] = tags


        ok = self.database.create_note(username, copy.deepcopy(note_data))
        if ok:
            return (note_data, True)
        return ('unable to create note', False)


    def delete_note(self, username, key):
        data = self.database.delete_note(username, key)
        return data


    def notes_index(self, username, length, since, mark):
        """ username<string>, length<int>, since<float>, mark<whatever> """
        data, status = self.database.notes_index(username, length, since, mark)
        return (data, status)

    # TODO: tags api



    def _validate_tag(self, t):

        # remove surrounding whitespace
        t = t.strip()

        # can't contain whitespace or commas!
        if re.search(r'(\s|,)', t):
            return None

        return t






