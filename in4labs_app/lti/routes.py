import os
import pprint

from flask import session, jsonify, redirect, url_for  
from flask_login import login_user

from pylti1p3.contrib.flask import FlaskOIDCLogin, FlaskRequest, FlaskCacheDataStorage
from pylti1p3.tool_config import ToolConfDict
from pylti1p3.registration import Registration

from . import bp
from .utils import ExtendedFlaskMessageLaunch
from .. import app, db, cache
from ..config import Config
from ..models import User


def get_lti_config_path():
    return os.path.join(app.root_path, '..', 'configs', 'app.json')


def get_launch_data_storage():
    return FlaskCacheDataStorage(cache)


def log_user(user_email):
    user = User.query.filter_by(email=user_email).first()
    if user is None: 
        # Register the user if doesn't exist
        user= User(email=user_email)
        db.session.add(user)
        db.session.commit()
    login_user(user, remember=False)


@bp.route('/jwks/', methods=['GET'])
def get_jwks():
    tool_conf = ToolConfDict(Config.lti_config)
    # return jsonify({'keys': tool_conf.get_jwks()})
    return jsonify(tool_conf.get_jwks()) # for Moodle compatibility


@bp.route('/login/', methods=['GET', 'POST'])
def login():
    tool_conf = ToolConfDict(Config.lti_config)
    launch_data_storage = get_launch_data_storage()

    flask_request = FlaskRequest()
    target_link_uri = flask_request.get_param('target_link_uri')
    if not target_link_uri:
        raise Exception('Missing "target_link_uri" param')

    oidc_login = FlaskOIDCLogin(flask_request, tool_conf, launch_data_storage=launch_data_storage)
    return oidc_login\
        .enable_check_cookies()\
        .redirect(target_link_uri)


@bp.route('/launch/', methods=['POST'])
def launch():
    tool_conf = ToolConfDict(Config.lti_config)
    flask_request = FlaskRequest()
    launch_data_storage = get_launch_data_storage()
    message_launch = ExtendedFlaskMessageLaunch(flask_request, tool_conf, launch_data_storage=launch_data_storage)
    message_launch_data = message_launch.get_launch_data()
    session['message_launch_data'] = message_launch_data
    pprint.pprint(message_launch_data)

    user_email = message_launch_data.get('email')
    if user_email:
        log_user(user_email)

    return redirect(url_for('index'))

