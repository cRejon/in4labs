from flask_login import login_user
from pylti1p3.contrib.flask import FlaskMessageLaunch, FlaskCacheDataStorage

from .. import db, cache
from ..app_bp.models import User
from ..config.config import Config


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
        if iss == Config.MOODLE_HOST: # Problem with Moodle nonce too
            return self
        return super().validate_nonce()