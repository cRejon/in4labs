from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from in4labs_app import login
from in4labs_app import db


class LTIConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    iss = db.Column(db.Text)
    client_id = db.Column(db.Text)
    auth_login_url = db.Column(db.Text)
    auth_token_url = db.Column(db.Text)
    key_set_url = db.Column(db.Text)
    private_key_file = db.Column(db.Text)
    public_key_file = db.Column(db.Text)
    public_jwk = db.Column(db.Text)
    deployment_id = db.Column(db.Text)


class User(UserMixin,db.Model):
    id=db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    email=db.Column(db.String(64), nullable=False,unique=True)
    session_data = db.Column(db.Text)

    def __repr__(self):
        return f'<User {self.email}>'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Reservation(db.Model):
    id=db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    user=db.Column(db.Integer, nullable=False)
    date_time=db.Column(db.DateTime, nullable=False, unique=True)

