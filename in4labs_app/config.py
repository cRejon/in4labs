import os
from tempfile import mkdtemp


basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    # Flask settings
    ENV = 'development'
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 600
    SECRET_KEY = 'replace-me', # change in production
    SESSION_TYPE= 'filesystem',
    SESSION_FILE_DIR = mkdtemp(),
    SESSION_COOKIE_NAME = 'app-sessionid' 
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False   # should be True in case of HTTPS usage (production)
    SESSION_COOKIE_SAMESITE = None  # should be 'None' in case of HTTPS usage (production)
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'in4labs.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # LTI settings
    # Replace the values with the ones from your LMS as explained in the README
    MOODLE_HOST = ''
    CLIENT_ID = ''
    DEPLOYMENT_ID = ''
    lti_config = {
        f'http://{MOODLE_HOST}/moodle': [{
            'default': True,
            'client_id': CLIENT_ID,
            'auth_login_url': f'http://{MOODLE_HOST}/moodle/mod/lti/auth.php',
            'auth_token_url': f'http://{MOODLE_HOST}/moodle/mod/lti/token.php',
            'auth_audience': None,
            'key_set_url': f'http://{MOODLE_HOST}/moodle/mod/lti/certs.php',
            'key_set': None,
            'private_key_file': None,
            'public_key_file': None,
            'deployment_ids': [DEPLOYMENT_ID]
        }]
    }

    # Labs settings
    labs_config = {
        'duration': 10, # minutes
        'labs': [{
            'lab_name' : 'lab_1',
            'html_name' : 'Laboratory 1',
            'description' : 'Example of a remote laboratory for Arduino.',
            'host_port' : 8001,
            'nat_port' : 8881,
            'cam_url': 'http://ULR_TO_WEBCAM/Mjpeg',
        }, {
            'lab_name' : 'lab_2',
            'html_name' : 'Laboratory 2',
            'description' : 'Example of a remote laboratory for Jupyter Notebook.',
            'host_port' : 8002,
            'nat_port' : 8882,
        }],
    }