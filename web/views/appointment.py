from datetime import datetime

from flask import render_template, url_for, request
from flask_classful import FlaskView
from werkzeug.utils import redirect

from connectors import ImpzentrenBayerConnector, UsernamePasswordLoginProvider, InvalidCredentialsException
from entities import Appointment
from web.views.base import WithConnector


class AppointmentsView(FlaskView, WithConnector):

    def index(self):
        try:
            if self.connector.has_next_appointment():
                return f'already has an appointment {self.connector.get_current_appointment()}'
            appointments = self.connector.get_appointments_in_range(datetime.now().date(), days=30)
            return render_template('appointments.html', appointments=appointments)
        except InvalidCredentialsException:
            return redirect(url_for('HomeView:index'))

    def post(self):
        appointment = Appointment.from_json(request.form)
        self.connector.book_appointment(appointment)
        return f'booked {appointment}'
