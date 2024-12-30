import pprint

from flask import session, jsonify, redirect, url_for  

from pylti1p3.contrib.flask import FlaskOIDCLogin, FlaskRequest
from pylti1p3.tool_config import ToolConfDict

from . import bp
from .utils import ExtendedFlaskMessageLaunch, get_launch_data_storage, log_user
from ..config.config import Config


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
    #pprint.pprint(message_launch_data)

    user_email = message_launch_data.get('email')
    if user_email:
        log_user(user_email)

    lab_name = message_launch_data.get('https://purl.imsglobal.org/spec/lti/claim/custom', {}).get('lab', None)

    return redirect(url_for('app.book_lab', lab_name=lab_name))

