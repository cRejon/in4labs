import os
import time
from datetime import datetime, timedelta, timezone

from flask import session, request, redirect, render_template, url_for, flash, jsonify
from flask_login import  current_user, login_required

import docker

from . import bp
from .models import Booking
from .utils import StopContainersTask, setup_node_red, get_lab
from .. import db
from ..config.config import Config


basedir = os.path.abspath(os.path.dirname(__file__))
lab_duration = Config.labs_config['duration']
url_prefix = '/' + Config.labs_config['server_name']

# Check a timeslot availability with AJAX
@bp.route('/check_slot')
@login_required
def check_slot():
    lab_name = request.args.get('lab_name') # not used because actual labs are exclusive
    user_datetime = datetime.fromisoformat(request.args.get('user_datetime'))
    formatted_user_datetime = user_datetime.strftime('%d/%m/%Y @ %H:%Mh')
    utc_user_datetime = user_datetime.astimezone(timezone.utc)

    # Check if date_time is outdate
    actual_minute = datetime.now(timezone.utc).minute
    round_minute = actual_minute - (actual_minute % lab_duration)
    round_date_time = datetime.now(timezone.utc).replace(minute=round_minute, second=0, microsecond=0)
    if utc_user_datetime < round_date_time:
        response = f'''The date and time you selected ({formatted_user_datetime}) 
                       is outdate, please select a different one.'''
        return jsonify(response)

    booking = Booking.query.filter_by(date_time=utc_user_datetime).first()
    #booking = Booking.query.filter_by(lab_name=lab_name, date_time=utc_user_datetime).first()
    if booking is not None: # time slot is already booked
        response = f'''Time slot for {formatted_user_datetime} is already 
                       reserved, please select a different one.'''
    else:
        response = f'''Time slot for {formatted_user_datetime} is available.
                        Do you want to reserve the Lab? '''
         
    return jsonify(response)

from .forms import BookingForm
@bp.route('/<lab_name>/book/', methods=['GET', 'POST'])
@login_required
def book_lab(lab_name):
    lab = get_lab(lab_name)
    
    form = BookingForm(lab_duration)
    if form.validate_on_submit():
        user_datetime = datetime.fromisoformat(form.date_time.data)
        formatted_user_datetime = user_datetime.strftime('%d/%m/%Y @ %H:%Mh')
        utc_user_datetime = user_datetime.astimezone(timezone.utc)
        # For security reasons, check again if the time slot is still available
        booking = Booking.query.filter_by(lab_name=lab_name, date_time=utc_user_datetime).first()
        if booking is not None: 
            flash('Someone has booked the Lab before you, please select a different time slot.', 'error')
            return redirect(url_for('app.book_lab', lab_name=lab_name))
        
        booking = Booking(user_id=current_user.id, lab_name=lab_name, date_time=utc_user_datetime)
        db.session.add(booking)
        db.session.commit()
        flash(f'{lab["html_name"]} reserved successfully for {formatted_user_datetime}', 'success')
        return redirect(url_for('app.book_lab', lab_name=lab_name))
    
    message_launch_data = session['message_launch_data']

    tpl_kwargs = {
        'lab': lab,
        'lab_duration': lab_duration,
        'url_prefix': url_prefix,
        'launch_data': message_launch_data,
        'user_email': message_launch_data.get('email'),
        'user_name': message_launch_data.get('name', ''),
        'form': form,
    }
    return render_template('book_lab.html', **tpl_kwargs)


@bp.route('/<lab_name>/enter/', methods=['GET'])
@login_required
def enter_lab(lab_name):
    lab = get_lab(lab_name) 
    
    actual_minute = datetime.now(timezone.utc).minute
    start_minute = actual_minute - (actual_minute % lab_duration)
    start_datetime = datetime.now(timezone.utc).replace(minute=start_minute, second=0, microsecond=0)
    booking = Booking.query.filter_by(lab_name=lab_name, date_time=start_datetime).first()

    if booking and (booking.user_id == current_user.id):
        client = docker.from_env()
        server_name = Config.labs_config['server_name']    
        hostname = request.headers.get('Host').split(':')[0]
        lab_url = f'https://{hostname}/{server_name}/{lab_name}/'
        # Create a unique container name with the lab name and the start date time
        container_name = f'{lab_name.lower()}-{start_datetime.strftime("%Y%m%d%H%M")}'

        # Check if the actual time slot container is already running (e.g. the user click twice on the Enter button).
        # If so, redirect to the container url. If not, start the container
        try:
            container = client.containers.get(container_name)
            return redirect(lab_url)
        except docker.errors.NotFound:
            pass 
        
        # NOTE: The thread created by the StopContainersTask class sometimes doesn't stop the lab container,
        # so check if there is any previous container running and stop it  
        try:
            containers = client.containers.list()
            for container in containers:
                if container.name.startswith(lab_name.lower()):
                    container.stop()
        except docker.errors.NotFound:
            pass
        
        containers = []
        # Check if the lab needs extra containers and start them
        extra_containers = lab.get('extra_containers', [])
        for extra_container in extra_containers:
            # Setup the node-red container
            if extra_container['name'] == 'node-red':
                volume_name = list(extra_container['volumes'].keys())[0]
                nodered_dir = os.path.join(basedir, 'labs', lab_name, 'node-red')
                setup_node_red(client, volume_name, nodered_dir, current_user.email)

            container_extra = client.containers.run(
                            extra_container['image'], 
                            name=extra_container["name"],
                            detach=True,
                            remove=True,
                            ports=extra_container['ports'],
                            volumes=extra_container.get('volumes', {}),
                            network=extra_container.get('network', ''),
                            command=extra_container.get('command', ''))
            containers.append(container_extra)
        
        # Run the lab container
        lab_url_prefix = url_prefix + '/' + lab_name
        lab_image_name = f'{lab_name.lower()}:latest'
        host_port = lab['host_port'] 
        default_volume = {'/dev/bus/usb': {'bind': '/dev/bus/usb', 'mode': 'rw'}}
        lab_volumes = default_volume.update(lab.get('volumes', {}))
        node_red_url = f'https://{hostname}/{server_name}/{lab_name}/node-red/'
        end_time = start_datetime + timedelta(minutes=lab_duration)
        docker_env = {
            'URL_PREFIX': lab_url_prefix,
            'USER_EMAIL': current_user.email,
            'END_TIME': end_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'CAM_URL': lab.get('cam_url', ''),
            'NODE_RED_URL': node_red_url,
        }

        container_lab = client.containers.run(
                        lab_image_name, 
                        name=container_name,
                        detach=True, 
                        remove=True,
                        privileged=True,
                        volumes=lab_volumes,
                        ports={'8000/tcp': ('0.0.0.0', host_port)}, 
                        environment=docker_env)
        containers.append(container_lab)

        stop_containers = StopContainersTask(lab_name, containers, end_time, current_user.email)
        stop_containers.start()
        time.sleep(1) # Wait for the containers to start
        return redirect(lab_url)

    else:
        flash('You don´t have a reservation for the actual time slot, please make a booking.', 'error')
        return redirect(url_for('app.book_lab', lab_name=lab_name))


