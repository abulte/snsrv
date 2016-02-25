
# high level db access
# must define lowerlevel db something...

import datetime
import uuid

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



    
