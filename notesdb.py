

import uuid
import time
import re
import pymongo

class NotesDB():
    def __init__(self, database):
        # connect to database
        # setup variables
        self.database = database
        self.re_float = re.compile(r'^(\d+\.\d+|\d+)$')
        self.re_int = re.compile(r'^\d+$')


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
             return (404, "cannot update: note not found")


        # save the data from the old version for future use
        old_version = {}
        new_version = False



        # increment version
        note['syncnum'] = note['syncnum'] + 1

        # update content and tags. TODO: sanitize/verify all data
        if 'content' in data:
            cont = str(data['content'])

            if note['content'] != cont: # ie changed data

                old_version['content'] = note['content']
                old_version['versiondate'] = note['modifydate']
                old_version['version'] = note['version']
                old_version['key'] = note['key']
                new_version = True

                note['content'] = cont
                note['version'] = note['version'] + 1 # inc version since new content

        if 'tags' in data:
            note['tags'] = [str(t) for t in data['tags']]

        # use given modifydate if possible. 
        if 'modifydate' in data:
            t = self._verify_time(data['modifydate'])
            if not t: return (403, "invalid modifydate")
            note['modifydate'] = t
        else:
            note['modifydate'] = time.time()

        if 'deleted' in data:
            d = str(data['deleted'])
            if d == "0" or d == "1":
                note['deleted'] = int(d)
            else:
                # invalid data, abort
                return (403, "invalid deleted property")

        if 'systemtags' in data:
            t = data['systemtags']
            # TODO: better verification, does simplenote support more systemtags?
            if t == ['markdown'] or t == []:
                note['systemtags'] = t
            else:
                # invalid data, abort
                return (403, "invalid system tags")

        self.database.update({'_id': note['_id']}, note)

        if new_version:
            self.database.insert(old_version)

        note.pop('_id', None)
        return (200, note)


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
            note['tags'] = []

        if 'modifydate' in data:
            t = self._verify_time(data['modifydate'])
            if not t: return (403, "invalid modifydate")
            note['modifydate'] = t
        else:
            note['modifydate'] = time.time()

        if 'createdate' in data:
            t = self._verify_time(data['createdate'])
            if not t: return (403, "invalid createdate")
            note['createdate'] = t
        else:
            note['createdate'] = time.time()


        note['deleted'] = 0
        note['version'] = 0
        note['systemtags'] = []
        note['syncnum'] = 1

        self.database.insert(note)
        note.pop('_id', None)
        return (200, note)


    def delete_note(self, note_id):
        # permanently delete the note (and all versions) from database

        note = self.get_note(note_id)
        if not note:
            return (404, "note not found") # not found
        if note['deleted'] != 1:
            return (403, "send to trash before deleting") # not trashed yet!

        print(note)

        result = self.database.remove({'key': note_id})

        # something failed
        if not result['ok']:
            return (500, "unknown error")

        # couldn't find any to delete
        if result['n'] == 0:
            return (404, "note not found") # not found

        # otherwise, all good :)
        return (200, "")

    def list_notes(self, length=None, since=None, mark=None):
        """return (status, data) where data is list of notes that fit criteria if status ok, or error string if not ok """

        exclude = {
                '_id': 0,
                'content': 0
                }

        if since is not None:
            if self.re_float.match(since):
                # get the whole list with date greater than since
                since = float(since)
                notes = self.database.find({'modifydate': {'$gt':since}}, exclude)
            else:
                return (403,"invalid since date") 
        else:
            notes = self.database.find({'modifydate': {'$exists':True}}, exclude)

        # sort by date
        notes.sort([('modifydate', pymongo.ASCENDING)])


        # skip over marked notes
        if mark is not None:
            if self.re_int.match(mark):
                start = int(mark)
                if start >= len(notes):
                    return (403,"invalid mark") 
                else:
                    notes.skip(start)
            else:
                return (403,"invalid mark") 

        # limit to length
        if length is not None:
            if self.re_int.match(length):
                length = int(length)
                # filter by length
                notes.limit(length)
            else:
                return (403,"invalid length") 

        notes_list = list(notes)
        count = len(notes_list)
        the_time = str(time.time())

        #TODO limit and do stuff with mark

        return (200, {'count': count, 'data':notes_list, 'time':the_time})



        


    def _genkey(self):
        """Generates a unique key for a new note to go in the database"""

        while True:
            key = str(uuid.uuid4())
            print(key)
            if not self.database.find_one({'key': key}):
                return key


    def _verify_time(self, t):
        """checks that the time in str 't' is valid (time since epoch in seconds)
           Returns float(t) if valid, else None
        """
        if isinstance(t,float) or isinstance(t,int):
            pass
        elif isinstance(t,str):
            if self.re_float.match(t): # check valid float/int value
                t = float(t)
        else:
            return None
        
        if t <= time.time(): #  check not in the future
            return t

        return None










