
# high level db access
# must define lowerlevel db something...

import datetime

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

    def get_note(self, userid, noteid, version=None):
        note = self.database.get_note(noteid, version)
        if not note or note['userid'] != userid:
            # TODO: +future +enhancement check for share key to allow sharing notes around users
            return None
        return note



    
