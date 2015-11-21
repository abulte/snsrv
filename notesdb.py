

import uuid
import time

class NotesDB():
    def __init__(self, database):
        # connect to database
        # setup variables
        self.database = database


    def get_note(self, note_id, version=None):
        # return correct note at version


        # if version given, return the versioned note, else return the main note
        if version is not None:
            note = self.database.find_one({'key': note_id, 'version': version})
        else:
            note = self.database.find_one({'key': note_id, 'createdate': {'$exists':True}})

        if not note:
            return None
        note.pop('_id', None)
        return note



    def update_note(self, note_id, data):
        # update note_id with data
        # find highest note version, make new note with incremented version and new/updated content

        note = self.database.find_one({'key': note_id, 'createdate': {'$exists':True}})
        if not note:
             # can't update a non-existant note!
             return None


        # save the data from the old version for future use
        old_version = {}
        old_version['content'] = note['content']
        old_version['versiondate'] = note['modifydate']
        old_version['version'] = note['version']
        old_version['key'] = note['key']



        # increment version
        note['version'] = note['version'] + 1

        # update content and tags. TODO: sanitize data
        if 'content' in data:
            note['content'] = data['content']
        if 'tags' in data:
            note['tags'] = data['tags']

        # use given modifydate if possible. TODO: verify date
        if 'modifydate' in data:
            note['modifydate'] = data['modifydate']
        else:
            note['modifydate'] = str(time.time())

        if 'deleted' in data:
            d = data['deleted']
            if d == 0 or d == 1:
                note['deleted'] = d
            else:
                # invalid data, abort
                return None

        if 'systemtags' in data:
            t = data['systemtags']
            # TODO: better verification, does simplenote support more systemtags?
            if t == ['markdown'] or t == []:
                note['systemtags'] = t
            else:
                # invalid data, abort
                return None

        self.database.update({'_id': note['_id']}, note)
        self.database.insert(old_version)

        note.pop('_id', None)
        return note


    def create_note(self, data):
        # create a new note with the given data (note content and tags?)

        note = {}

        key = self._genkey()

        note['key'] = key

        #TODO: sanitize all data
        if 'content' in data:
            note['content'] = data['content']
        else:
            note['content'] = ''
        if 'tags' in data:
            note['tags'] = data['tags']
        else:
            note['content'] = []

        if 'modifydate' in data:
            note['modifydate'] = data['modifydate']
        else:
            note['modifydate'] = str(time.time())

        if 'createdate' in data:
            note['createdate'] = data['createdate']
        else:
            note['createdate'] = str(time.time())


        note['deleted'] = 0
        note['version'] = 0
        note['versiondate'] = str(time.time())
        note['systemtags'] = []

        self.database.insert(note)
        note.pop('_id', None)
        return note


    def _genkey(self):
        """Generates a unique key for a new note to go in the database"""

        while True:
            key = str(uuid.uuid4())
            print(key)
            if not self.database.find_one({'key': key}):
                return key


