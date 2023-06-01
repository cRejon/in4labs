from flask import Blueprint

bp = Blueprint('lti', __name__,)

from . import routes