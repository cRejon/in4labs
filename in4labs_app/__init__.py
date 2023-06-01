import os
import threading
import time
from datetime import datetime, timedelta

from flask import Flask, session, request, redirect, render_template, url_for, flash
from flask_login import LoginManager, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache

import docker

from .config import Config


db = SQLAlchemy()
login = LoginManager()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object(Config)
basedir = os.path.abspath(os.path.dirname(__file__))

cache = Cache(app)

from .lti.utils import ReverseProxied
app.wsgi_app = ReverseProxied(app.wsgi_app)

# init login
login.init_app(app)

# init sqlalchemy
db.init_app(app)

# create db if not exists
from .models import User, Booking
if not os.path.exists(os.path.join(basedir, 'in4labs.db')): 
    print("Creating database...")
    with app.app_context():
        db.create_all() # create tables in db

# create docker image if not exists
client = docker.from_env()
image_name = Config.DOCKER_IMAGE_NAME
image_tag = "latest"
try:
    client.images.get(f"{image_name}:{image_tag}")
except docker.errors.ImageNotFound:
    print(f"Creating Docker image {image_name}:{image_tag}.")
    dockerfile_path = os.path.join(basedir, 'docker')
    image, build_logs = client.images.build(
        path=dockerfile_path,
        tag=f"{image_name}:{image_tag}",
        rm=True,
    )
    for log in build_logs: # Print the build logs for debugging purposes
        print(log.get("stream", "").strip())

# add blueprint for LTI
from . import lti
app.register_blueprint(lti.bp)


@app.before_request
def before_request():
    # clear database from expired bookings
    Booking.query.filter(Booking.date_time < datetime.now()-timedelta(minutes=Config.LAB_DURATION)).delete()
    db.session.commit()

from .forms import BookingForm
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = BookingForm(Config.LAB_DURATION)
    if form.validate_on_submit():
        date_time = datetime.combine(form.date.data, form.hour.data)
        booking = Booking.query.filter_by(date_time=date_time).first()
        if booking is not None: # time slot is already booked
            flash('This time slot is already reserved, please select a different one.', 'error')
            return redirect(url_for('index'))
        booking = Booking(user_id=current_user.id, date_time=date_time)
        db.session.add(booking)
        db.session.commit()
        flash(f'Lab reserved successfully for {date_time.strftime("%d/%m/%Y @ %H:%Mh.")}', 'success')
        return redirect(url_for('index'))
    
    message_launch_data = session['message_launch_data']

    # Possibility to get custom params
    custom_param = message_launch_data.get('https://purl.imsglobal.org/spec/lti/claim/custom', {}) \
        .get('custom_param', None)

    tpl_kwargs = {
        'page_title': Config.PAGE_TITLE,
        'lab_name': Config.LAB_NAME,
        'lab_duration': Config.LAB_DURATION,
        'launch_data': message_launch_data,
        'curr_user_email': message_launch_data.get('email'),
        'curr_user_name': message_launch_data.get('name', ''),
        'form': form,
    }
    return render_template('index.html', **tpl_kwargs)


@app.route('/lab/', methods=['GET'])
@login_required
def lab():
    minute = datetime.now().minute
    round_minute = minute - (minute % Config.LAB_DURATION)
    round_date_time = datetime.now().replace(minute=round_minute, second=0, microsecond=0)
    booking = Booking.query.filter_by(date_time=round_date_time).first()
    if booking and (booking.user_id == current_user.id):
        end_time = round_date_time + timedelta(minutes=Config.LAB_DURATION)
        docker_config = {
            'USER_EMAIL': session['message_launch_data'].get('email'),
            'USER_ID': current_user.id,
            'END_TIME': end_time.strftime('%Y-%m-%dT%H:%M:%S'),
        }
        port = 5001
        container = client.containers.run(f'{image_name}:{image_tag}', detach=True, remove=True,
                                            ports={'80/tcp': ('0.0.0.0', port)}, environment=docker_config)

        remaining_secs = (end_time - datetime.now()).total_seconds()
        stop_container = StopContainerTask(container, remaining_secs)
        stop_container.start()
        
        hostname = request.headers.get('Host').split(':')[0]
        container_url = f'http://{hostname}:{port}'
        return redirect(container_url)
    
    flash('You don´t have a reservation for the actual time slot, please make a booking.', 'error')
    return redirect(url_for('index'))

 
class StopContainerTask(threading.Thread):
     def __init__(self, container, remaining_secs):
         super(StopContainerTask, self).__init__()
         self.container = container
         self.remaining_secs = remaining_secs
 
     def run(self):
        # minus 2 seconds for safety
        time.sleep(self.remaining_secs - 2)
        self.container.stop()
        print('Container stopped.')
