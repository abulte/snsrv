
# Template for database class

class DB(object):
    def __init__(self, args):
        pass

    def first_run(self):
        raise NotImplemented()

    def get_user(self, email):
        """ should return a dictionary containing email/username, hashed password, token, token expiry date, id """
        raise NotImplemented()

    def create_user(self, email, hashed):
        """ creates a new user with the supplied email and hashed password
            returns true if worked ok, else false
        """
        raise NotImplemented()

    def update_token(self, email, token, tokendate):
        """ set the new api auth token in the database """
        raise NotImplemented()

    def create_note(self, email, note_data):
        """ creates a new note in the database - given email (user login) and a dictionary of given notedata
            returns true if able to put in database
        """
        raise NotImplemented()

    def get_note(self, email, key, version=None):
        """ returns the note by key (and correct version) - returns none if not found """
        raise NotImplemented()

    def update_note(self, email, note_data):
        """ update the note given by note_data """
        raise NotImplemented()

    def delete_note(self, email, key):
        """
            delete the note by key and username
            returns (status-or-dictionary-data, http-status-code)
        """
        raise NotImplemented()

    def save_version(self, email, notekey):
        """ save the current notekey as a version """
        raise NotImplemented()

    # this does not have to verify user ownership
    def drop_old_versions(self, email, notekey, minversion):
        """ delete all note versions below the minversion """
        raise NotImplemented()


    def notes_index(self, email, length, since, mark):
        """
            get the notes index (list of notes with partial data)
            returns (status-or-dictionary-data, http-status-code)
        """
        raise NotImplemented()

