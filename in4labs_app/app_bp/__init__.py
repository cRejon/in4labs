from flask import Blueprint

bp = Blueprint('app', __name__)

# add blueprint for LTI
from .. import lti
bp.register_blueprint(lti.bp, url_prefix='/lti')

from . import routes