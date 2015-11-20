

import pymongo

class NotesDB():
    def __init__(self, database):
        # connect to database
        # setup variables
        self.database = database


    def get_note(self, note_id, version=None):
        # return correct note at version

        if version is not None:
            result = self.database.find_one({'key': note_id, 'version': version})
            if not result:
                return None
            note = result
            
        else:
            result = self.database.find({'key': note_id})

            if not result:
                return None

            result.sort([('version', pymongo.ASCENDING)])
            note = result.next()

        note.pop('_id', None)
        return note



    def update_note(self, note_id, data):
        # update note_id with data
        return note_id
