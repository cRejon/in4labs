import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache

from .config.config import Config

# Set the base directory to the current file's directory
basedir = os.path.abspath(os.path.dirname(__file__))

# Get variables from config
server_name = Config.labs_config['server_name']
mountings = Config.labs_config['mountings']
labs = Config.labs_config['labs']

app = Flask(__name__, template_folder='templates', static_folder='static',
            static_url_path=(f'/{server_name}/static/'))
app.config.from_object(Config)

cache = Cache(app)

if app.config['ENV'] == 'production': 
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
    )

# Init login
login = LoginManager()
login.init_app(app)

# Init sqlalchemy
db = SQLAlchemy()
db.init_app(app)

# Create db if not exists
from .app_bp.models import User, Booking
if not os.path.exists(os.path.join(basedir, 'in4labs.db')): 
    print('Creating database...')
    with app.app_context():
        db.create_all() # create tables in db

# Copy html files with lab instructions to templates folder
for lab in labs:
    lab_name = lab['lab_name']
    html_path = os.path.join(basedir, 'labs', lab_name, 'instructions.html')
    if os.path.exists(html_path):
        html_dest = os.path.join(basedir, 'templates', f'{lab_name}_instructions.html')
        with open(html_path, 'r') as f:
            html_content = f.read()
        with open(html_dest, 'w') as f:
            f.write(html_content)

# Register blueprints - moved to the end to avoid circular imports
def register_blueprints():
    from . import app_bp, lti
    app.register_blueprint(app_bp.bp, url_prefix=f'/{server_name}')
    app.register_blueprint(lti.bp, url_prefix=f'/{server_name}/lti')

register_blueprints()