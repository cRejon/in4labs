from flask_wtf import FlaskForm
from wtforms import TimeField, SubmitField, DateField
from wtforms.validators import ValidationError, DataRequired
from in4labs_app.models import Reservation
from datetime import datetime, time


class ReservationForm(FlaskForm):
    date = DateField('Date', 
                    format='%Y-%m-%d', 
                    default=datetime.now(),
                    validators=[DataRequired()])
    hour = TimeField('Hour', 
                    format='%H:%M', 
                    default= time(hour=(datetime.now().hour), minute=0),
                    validators=[DataRequired()])
    submit = SubmitField('Check')

    def validate_time_slot(self, hour):
        if hour.data.minute != 0:
            raise ValidationError('Select an o´clock hour (eg. 14:00).')
        
        date_time = datetime.combine(self.date.data, hour.data)
        reservation = Reservation.query.filter_by(date_time=date_time).first()
        if reservation is not None: # time slot is already reserved
            raise ValidationError('This time slot is already reserved, please select a different one.')