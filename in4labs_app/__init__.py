import datetime
import os
import pprint

from tempfile import mkdtemp
from flask import Flask, session, jsonify, redirect, render_template, url_for, flash
from flask_login import LoginManager, current_user, login_required, login_user
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_migrate import Migrate

from werkzeug.exceptions import Forbidden

from pylti1p3.contrib.flask import FlaskOIDCLogin, FlaskMessageLaunch, FlaskRequest, FlaskCacheDataStorage
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.registration import Registration

from dotenv import dotenv_values
import docker

from in4labs_app.models import Reservation
from in4labs_app.forms import ReservationForm


class ReverseProxied:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        scheme = environ.get('HTTP_X_FORWARDED_PROTO')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)


app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_pyfile("config.py")
#app.secret_key = app.config["SECRET_KEY"]
app.wsgi_app = ReverseProxied(app.wsgi_app)
cache = Cache(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager()


# init sqlalchemy
db.init_app(app)
basedir = os.path.abspath(os.path.dirname(__file__))
if not os.path.exists('sqlite:///' + os.path.join(basedir, 'iot_lab.db')): 
    from .models import User
    from .models import Reservation
    with app.app_context():
        db.create_all() # create tables in db

# init login
login.init_app(app)

# setup config
config = {
    "DEBUG": True,
    "ENV": "development",
    "CACHE_TYPE": "simple",
    "CACHE_DEFAULT_TIMEOUT": 600,
    "SECRET_KEY": "replace-me",
    "SESSION_TYPE": "filesystem",
    "SESSION_FILE_DIR": mkdtemp(),
    "SESSION_COOKIE_NAME": "in4labs-app-sessionid",
    "SESSION_COOKIE_HTTPONLY": True,
    "SESSION_COOKIE_SECURE": False,   # should be True in case of HTTPS usage (production)
    "SESSION_COOKIE_SAMESITE": None,  # should be 'None' in case of HTTPS usage (production)
    "DEBUG_TB_INTERCEPT_REDIRECTS": False
}
app.config.from_mapping(config)
cache = Cache(app)

PAGE_TITLE = 'In4Labs'
LAB_NAME = 'IoT Lab'


class ExtendedFlaskMessageLaunch(FlaskMessageLaunch):

    def validate_nonce(self):
        """
        Probably it is bug on "https://lti-ri.imsglobal.org":
        site passes invalid "nonce" value during deep links launch.
        Because of this in case of iss == http://imsglobal.org just skip nonce validation.
        """
        iss = self.get_iss()
        deep_link_launch = self.is_deep_link_launch()
        if iss == "http://imsglobal.org" and deep_link_launch:
            return self
        return super().validate_nonce()


def get_lti_config_path():
    return os.path.join(app.root_path, '..', 'configs', 'app.json')


def get_launch_data_storage():
    return FlaskCacheDataStorage(cache)


def get_jwk_from_public_key(key_name):
    key_path = os.path.join(app.root_path, '..', 'configs', key_name)
    f = open(key_path, 'r')
    key_content = f.read()
    jwk = Registration.get_jwk(key_content)
    f.close()
    return jwk


def log_user(user_email):
    user = User.query.filter_by(email=user_email).first()
    if user is None: 
        # Register the user if doesn't exist
        user=User(email=user_email)
        db.session.add(user)
        db.session.commit()
    login_user(user)


@app.route('/jwks/', methods=['GET'])
def get_jwks():
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    # return jsonify({'keys': tool_conf.get_jwks()})
    return jsonify(tool_conf.get_jwks()) # Moodle issue


@app.route('/login/', methods=['GET', 'POST'])
def login():
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    launch_data_storage = get_launch_data_storage()

    flask_request = FlaskRequest()
    target_link_uri = flask_request.get_param('target_link_uri')
    if not target_link_uri:
        raise Exception('Missing "target_link_uri" param')

    oidc_login = FlaskOIDCLogin(flask_request, tool_conf, launch_data_storage=launch_data_storage)
    return oidc_login\
        .enable_check_cookies()\
        .redirect(target_link_uri)


@app.route('/launch/', methods=['POST'])
def launch():
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    flask_request = FlaskRequest()
    launch_data_storage = get_launch_data_storage()
    message_launch = ExtendedFlaskMessageLaunch(flask_request, tool_conf, launch_data_storage=launch_data_storage)
    message_launch_data = message_launch.get_launch_data()
    session['message_launch_data'] = message_launch_data
    pprint.pprint(message_launch_data)

    user_email = message_launch_data.get('email', '')
    log_user(user_email)

    return redirect(url_for('index'))


@app.route('/index/', methods=['GET'])
# @login_required
def index():
    reservation_form = ReservationForm()
    if reservation_form.validate_on_submit():
        date_time = datetime.combine(reservation_form.date.data, reservation_form.hour.data)
        reservation = Reservation(user=current_user.id, date_time=date_time)
        db.session.add(reservation)
        db.session.commit()
        flash(f'Lab reserved successfully for {date_time.strftime("%d-%m-%Y")} at {date_time.hour}:00h')
        return redirect(url_for('index'))
    
    message_launch_data = session['message_launch_data']
    # Possibility to get custom params
    custom_param = message_launch_data.get('https://purl.imsglobal.org/spec/lti/claim/custom', {}) \
        .get('custom_param', None)

    tpl_kwargs = {
        'page_title': PAGE_TITLE,
        'lab_name': LAB_NAME,
        'launch_data': message_launch_data,
        #'launch_id': message_launch.get_launch_id(),
        'curr_user_name': message_launch_data.get('name', ''),
        'curr_user_email': message_launch_data.get('email', ''),
        'reservation_form': reservation_form,
    }
    return render_template('index.html', **tpl_kwargs)


@app.route('/lab/', methods=['GET'])
# @login_required
def lab():
    date_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    reservation = Reservation.query.filter_by(date_time=date_time).first()
    if reservation and (reservation.user == current_user.id):
        # add user name and ID in container config
        docker_config = {
            **dotenv_values('docker/.env'),
            'USER_NAME': session['message_launch_data'].get('name'),
            'USER_ID': current_user.id,
        }
        client = docker.from_env()
        container = client.containers.run('nginx:latest', detach=True, 
                                          ports={'80/tcp': ('0.0.0.0', 0)}, environment=docker_config)
        port = container.attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
        container_url = f'http://localhost:{port}'
        return redirect(container_url)
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9001)