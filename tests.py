import os
import json
import base64
import unittest
import tempfile

from app import app
from sqlite_db import Database
from db_frontend import Database as DBFrontend


class SNSRVTestCase(unittest.TestCase):

    def setUp(self):
        self.username = 'user'
        self.password = 'secretsecret'
        self.token = None

        self.db_fd, self.db_file_path = tempfile.mkstemp()

        db_options = {
            'FILE': self.db_file_path,
            'INIT_SQL_FILE': 'init.sql'
        }

        backend = Database(db_options)
        backend.first_run()

        app.config['database'] = DBFrontend(backend)
        app.config['DB_TYPE'] = 'sqlite_db'
        app.config['DB_OPTIONS'] = db_options
        app.config['SECRET_KEY'] = 'secret'
        app.config['TESTING'] = True
        self.app = app.test_client()

        self._register()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_file_path)

    def _get_authentified_url(self, url):
        return '%s?email=%s&auth=%s' % (url, self.username, self.token)

    def _register(self, user=None, password=None):
        """Create test user

        Use the endpoint instead of direct DB call because of
        context hell with legacy app structure.
        """

        response = self.app.post('/register', data=dict(
            username=user if user else self.username,
            password=password if password else self.password
        ))

        return response

    def _login(self):

        encoded_login = 'email=%s&password=%s' % (self.username, self.password)
        encoded_login = base64.b64encode(bytes(encoded_login, 'utf-8'))

        response = self.app.post('/api/login', data=encoded_login)

        self.token = response.get_data(as_text=True)

        return response

    def _create_note(self, content='foobar'):

        data = json.dumps(dict(
            content=content
        ))

        url = self._get_authentified_url('/api2/data')
        response = self.app.post(url, data=data)

        return response

    def test_register(self):

        response = self._register(user='anotheruser')
        self.assertIn('Redirecting...', response.get_data(as_text=True))

    def test_register_wrong_pw_len(self):

        response = self._register(user='anotheruser', password='123')
        self.assertIn('password must 8 or more characters', response.get_data(as_text=True))

    def test_register_with_existing_username(self):

        response = self._register()
        self.assertIn('Try again!', response.get_data(as_text=True))

    def test_protected_page_with_wrong_username(self):

        self.username = 'whatever'
        response = self.app.get(self._get_authentified_url('/api2/index'))
        self.assertIn('invalid credentials', response.get_data(as_text=True))

    def test_protected_page_with_good_username_wrong_token(self):

        self.token = 'xxx'
        response = self.app.get(self._get_authentified_url('/api2/index'))
        self.assertIn('invalid credentials', response.get_data(as_text=True))

    def test_protected_page_with_no_credentials(self):

        response = self.app.get('/api2/index')
        self.assertIn('missing credentials', response.get_data(as_text=True))

    def test_login(self):

        response = self._login()
        self.assertEqual(response.status_code, 200)

    def test_login_bad_creds(self):

        self.username = 'foo'
        self.password = 'bar'
        response = self._login()
        self.assertEqual(response.status_code, 401)

    def test_list_notes_empty(self):

        self._login()
        response = self.app.get(self._get_authentified_url('/api2/index'))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data, {
            'count': 0,
            'data': []
        })

    def test_create_note_with_invalid_data(self):

        self._login()

        url = self._get_authentified_url('/api2/data')
        response = self.app.post(url, data=dict(
            content='whatever'
        ))

        self.assertEqual(response.get_data(as_text=True), 'invalid json data')

    def test_create_note(self):

        self._login()
        response = self._create_note()

        data = json.loads(response.get_data(as_text=True))
        self.assertIn('content', data)
        self.assertEqual(data['content'], 'foobar')

    def test_list_notes_not_empty(self):

        self._login()
        self._create_note()

        response = self.app.get(self._get_authentified_url('/api2/index'))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['count'], 1)

    def test_get_note_detail(self):

        self._login()
        response = self._create_note()
        data = json.loads(response.get_data(as_text=True))
        note_id = data['key']

        response = self.app.get(self._get_authentified_url('/api2/data/%s' % note_id))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['content'], 'foobar')

    def test_get_note_detail_w_version(self):

        self._login()
        response = self._create_note()
        data = json.loads(response.get_data(as_text=True))
        note_id = data['key']

        # get version #1
        response = self.app.get(self._get_authentified_url('/api2/data/%s/1' % note_id))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['content'], 'foobar')

        # create version #2
        data = json.dumps({
            'content': 'new content'
        })
        response = self.app.post(self._get_authentified_url('/api2/data/%s' % note_id), data=data)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['version'], 2)
        self.assertEqual(data['content'], 'new content')

        # get version 2 details
        response = self.app.get(self._get_authentified_url('/api2/data/%s/2' % note_id))
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['content'], 'new content')

        # get version 1 again
        response = self.app.get(self._get_authentified_url('/api2/data/%s/1' % note_id))
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['content'], 'foobar')

        # get latest version (should be 2)
        response = self.app.get(self._get_authentified_url('/api2/data/%s' % note_id))
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['content'], 'new content')

    def test_get_note_detail_wrong_id(self):

        self._login()

        note_id = 'foobar'
        response = self.app.get(self._get_authentified_url('/api2/data/%s' % note_id))

        self.assertEqual(response.status_code, 404)

    def test_update_note(self):

        self._login()

        response = self._create_note()
        data = json.loads(response.get_data(as_text=True))
        note_id = data['key']

        data = json.dumps({
            'content': 'new content'
        })

        response = self.app.post(self._get_authentified_url('/api2/data/%s' % note_id), data=data)
        self.assertEqual(response.status_code, 200)

        response = self.app.get(self._get_authentified_url('/api2/data/%s' % note_id))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['content'], 'new content')

    def test_delete_note_wo_trash(self):

        self._login()

        response = self._create_note()
        data = json.loads(response.get_data(as_text=True))
        note_id = data['key']

        response = self.app.delete(self._get_authentified_url('/api2/data/%s' % note_id))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_data(as_text=True),
            'must send note to trash before permanently deleting'
        )

    def test_delete_note(self):

        self._login()

        response = self._create_note()
        data = json.loads(response.get_data(as_text=True))
        note_id = data['key']

        # move to trash
        data = json.dumps({
            'deleted': 1
        })
        response = self.app.post(self._get_authentified_url('/api2/data/%s' % note_id), data=data)
        self.assertEqual(response.status_code, 200)

        # delete
        response = self.app.delete(self._get_authentified_url('/api2/data/%s' % note_id))
        self.assertEqual(response.status_code, 200)

        # verify list is empty
        response = self.app.get(self._get_authentified_url('/api2/index'))
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data, {
            'count': 0,
            'data': []
        })

    def test_index_page(self):
        """Index is giving us something"""
        response = self.app.get('/')
        self.assertTrue('Welcome to SNSRV!' in response.get_data(as_text=True))

    def test_web_login(self):

        response = self.app.post('/login', data=dict(
            username=self.username,
            password=self.password
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('logout', response.get_data(as_text=True))

    def test_web_logout(self):

        self.test_web_login()
        response = self.app.get('/logout', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('login', response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
