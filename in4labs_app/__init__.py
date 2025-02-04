import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache

from .config.config import Config

basedir = os.path.abspath(os.path.dirname(__file__))

# Define the url_prefix to work with reverse proxy
url_prefix = '/' + Config.labs_config['server_name']

db = SQLAlchemy()
login = LoginManager()

app = Flask(__name__, static_url_path=(url_prefix+'/static/'))
app.config.from_object(Config)

cache = Cache(app)

from .app_bp.utils import ReverseProxied
#app.wsgi_app = ReverseProxied(app.wsgi_app)

if app.config['ENV'] == 'production':
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
    )

# Init login
login.init_app(app)

# Init sqlalchemy
db.init_app(app)

# Create db if not exists
from .app_bp.models import User, Booking
if not os.path.exists(os.path.join(basedir, 'in4labs.db')): 
    print('Creating database...')
    with app.app_context():
        db.create_all() # create tables in db

# Copy html files with lab instructions to templates folder
labs = Config.labs_config['labs']
for lab in labs:
    lab_name = lab['lab_name']
    html_path = os.path.join(basedir, 'labs', lab_name, 'instructions.html')
    if os.path.exists(html_path):
        html_dest = os.path.join(basedir, 'templates', f'{lab_name}_instructions.html')
        with open(html_path, 'r') as f:
            html_content = f.read()
        with open(html_dest, 'w') as f:
            f.write(html_content)

# Import blueprints
from . import app_bp
app.register_blueprint(app_bp.bp, url_prefix=url_prefix)
