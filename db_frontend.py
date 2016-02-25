
# high level db access
# must define lowerlevel db something...

import datetime
import uuid
import copy

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
        if user['token'] and user['token'] == token:
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

    def get_note(self, username, noteid, version=None):
        note = self.database.get_note(username, noteid, version)
        if not note:
            return None
        return note

    def update_note(self, userid, noteid, data):
        #TODO: check note exists, user can access, do stuff for data verification
        self.database.update_note(noteid, data)

    def create_note(self, username, data):
        note_data = {}
        if 'content' not in data:
            return ('note must contain a content field', False)
        note_data['content'] = str(data['content'])

        note_data['key'] = str(uuid.uuid4()) + str(int(datetime.datetime.utcnow().timestamp()))
        note_data['modifydate'] = datetime.datetime.utcnow()
        note_data['createdate'] = datetime.datetime.utcnow()
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
        




    def _validate_tag(self, t):

        # remove surrounding whitespace
        t = t.strip()

        # can't contain whitespace or commas!
        if re.search(r'(\s|,)', t):
            return None

        return t
            
        



    
