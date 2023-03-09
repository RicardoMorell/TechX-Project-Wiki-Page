from flaskr import create_app
from flask import url_for
from flask import Flask
from flaskr import backend
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from unittest.mock import patch
import base64
import io
import pytest

# See https://flask.palletsprojects.com/en/2.2.x/testing/ 
# for more info on testing

class MockUser:
    """A mock user on the wiki.
        
        This class will create a mock user object to mock the function of a user that is logged in.
        It will verify that the current user has been authenticated and is currently still logged in.
        This object will persist until the user is logged out.

        Attributes:
            username: A String containing the username of the user.
        """
    def __init__(self, username):
        """Initializes user with given username."""
        self.username = username

    def is_authenticated(self):
        """Indicates if the user is logged in or not.
        
        Returns:
            True to indicate that the user is still logged in
        """
        return True

    def get_id(self):
        """Passes user id when called.
            
        Returns:
            The username of the mock user as their user id
        """
        return self.username

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_home_page(client):
    """Tests the home page route by asserting that the home page is displayed."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"<div id='navigation-buttons'>" in resp.data

def test_login_page(client):
    """Tests the login route by asserting that the login page is displayed."""
    resp = client.get('/login')
    assert resp.status_code == 200
    assert b"<div id='login-page'>" in resp.data

def test_successful_login(client):
    """Tests the successful login path by creating mock Backend and User objects and asserting that user is logged in and redirected to home page."""
    with patch.object(backend.Backend, 'sign_in') as mock_sign_in:
        mock_sign_in.return_value = True

        with patch('flask_login.utils._get_user') as mock_get_user:
            mock_get_user.return_value = MockUser('test_user')

            resp = client.post('/login', data=dict(
                Username='test_user',
                Password='test_password'
            ), follow_redirects=True)

            assert resp.status_code == 200
            assert b"<div id='navigation-buttons'>" in resp.data
            assert mock_sign_in.called
            assert current_user.is_authenticated

def test_unsuccessful_login(client):
    """Tests the unsuccessful login path by creating a mock Backend object and asserting that error flash message is displayed."""
    with patch.object(backend.Backend, 'sign_in') as mock_sign_in:
        mock_sign_in.return_value = False

        resp = client.post('/login', data=dict(
            Username='test_user',
            Password='test_password'
        ), follow_redirects=True)

        assert resp.status_code == 200
        assert b"Invalid username or password. Please try again." in resp.data
        assert mock_sign_in.called

def test_logout(client):
    """Tests the logout route by creating a mock User object, logging them out, and asserting that logout page is displayed and user is no longer authenticated."""
    with patch('flask_login.utils._get_user') as mock_get_user:
        mock_get_user.return_value = MockUser('test_user')

        resp = client.post('/login', data=dict(
            Username='test_user',
            Password='test_password'
        ), follow_redirects=True)

        assert current_user.is_authenticated

        resp = client.get('/logout')
        assert mock_get_user.called
        assert resp.status_code == 200
        assert b"<div id='logout-message'>" in resp.data
        assert current_user.is_authenticated != True

def test_upload_page(client):
    """Tests the upload route by asserting that the upload page is displayed."""
    resp = client.get("/upload")
    assert resp.status_code == 200
    assert b"<div id='upload'>" in resp.data

def test_successful_upload(client):
    """Tests the successful upload path by creating a mock Backend object and mock File, and asserting that success flash message is displayed."""
    with patch.object(backend.Backend, 'upload') as mock_upload:
        mock_upload.return_value = True
        
        file_data = b'12345'
        file = io.BytesIO(file_data)
        file.filename = 'dummy_file.png'

        resp = client.post('/upload', data={
            'File name': 'dummy_file.png',
            'File': (file, 'dummy_file.png')
        }, content_type='multipart/form-data', follow_redirects=True)

        assert resp.status_code == 200
        assert mock_upload.called
        assert b"File uploaded successfully." in resp.data

def test_unsuccessful_upload(client):
    """Tests the unsuccessful upload path by creating a mock Backend object and mock File, and asserting that correct error flash message is displayed."""
    with patch.object(backend.Backend, 'upload') as mock_upload:
        mock_upload.return_value = False
        
        file_data = b'12345'
        file = io.BytesIO(file_data)
        file.filename = 'dummy_file.png'

        resp = client.post('/upload', data={
            'File name': 'dummy_file.png',
            'File': (file, 'dummy_file.png')
        }, content_type='multipart/form-data', follow_redirects=True)

        assert resp.status_code == 200
        assert mock_upload.called
        assert b"File name is taken." in resp.data

def test_no_file_upload(client):
    """Tests the "no file submitted" path by providing a name but no file, and asserting that correct error flash message is displayed."""
    resp = client.post('/upload', data={
            'File name': 'dummy_file.png',
        }, content_type='multipart/form-data', follow_redirects=True)

    assert resp.status_code == 200
    assert b"No file selected." in resp.data

def test_signup_page(client):
    """Tests the signup route by asserting that the signup page is displayed."""
    resp = client.get("/signup")
    assert resp.status_code == 200
    assert b"<div id='signup-page'>" in resp.data

def test_successful_signup(client):
    """Tests the successful signup path by creating a mock Backend object and asserting that success flash message is displayed."""
    with patch.object(backend.Backend, 'sign_up') as mock_sign_up:
        mock_sign_up.return_value = True

        resp = client.post('/signup', data=dict(
                Username='test_user',
                Password='test_password'
            ), follow_redirects=True)

        assert resp.status_code == 200
        assert b"Account successfully created! Please login to continue." in resp.data
        assert mock_sign_up.called

def test_unsuccessful_signup(client):
    """Tests the unsuccessful signup path by creating a mock Backend object and asserting that error flash message is displayed."""
    with patch.object(backend.Backend, 'sign_up') as mock_sign_up:
        mock_sign_up.return_value = False

        resp = client.post('/signup', data=dict(
                Username='test_user',
                Password='test_password'
            ), follow_redirects=True)

        assert resp.status_code == 200
        assert b"Username already exists. Please login or choose a different username." in resp.data
        assert mock_sign_up.called

def test_page_uploads(client):
    with patch.object(backend.Backend, 'get_wiki_page') as mock_get_wiki_page:
        #Set the return value of the mock method
        mock_content = 'Test wiki page content'
        mock_get_wiki_page.return_value = mock_content

        #Make a GET request to the test URL
        resp = client.get('/pages/TestPage')

        #check that the response status code is 200
        assert resp.status_code == 200
        
        #Check that the rendered HTML contains the mock content
        assert mock_content in resp.get_data(as_text=True)

        #Only reason it's navigation-buttons is because in the inspect the id is navigation-buttons
        assert b"<div id='navigation-buttons'>" in resp.data

def test_pages(client):
    #Mock the get_all_page_names method of the Backend class
    with patch.object(backend.Backend, 'get_all_page_names') as mock_get_all_page_names:
        #Set the return value of the mock method
        mock_page_names = ['Page1', 'Page2', 'Page3']
        mock_get_all_page_names.return_value = mock_page_names

        #Make a GET request to the test URL
        resp = client.get('/pages')

        #Check that the response status code is 200
        assert resp.status_code == 200

        assert b"<div id='display-pages'>" in resp.data

        #Check that the rendered HTML contains the mock page names
        for page_name in mock_page_names:
            assert page_name in resp.get_data(as_text=True)


