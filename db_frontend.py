
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
        if userdata['token']:
            # remove if over 24 hours old
            if (datetime.datetime.utcnow() - userdata['tokendate']).seconds > 86400:
                userdata['token'] = None
        else:
            userdate['token'] = None
        return userdata

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
        tokendate = datetime.datetime.utcnow()
        self.database.update_token(user['id'], token, tokendate)



    def get_note(self, userid, noteid, version=None):
        note = self.database.get_note(noteid, version)
        if not note or note['userid'] != userid:
            # TODO: +future +enhancement check for share key to allow sharing notes around users
            return None
        return note

    def update_note(self, userid, noteid, data):
        #TODO: check note exists, user can access, do stuff for data verification
        self.database.update_note(noteid, data)



    
