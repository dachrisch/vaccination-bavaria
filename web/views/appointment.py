from datetime import datetime

from flask import render_template, url_for, request, session
from flask_classful import FlaskView
from werkzeug.utils import redirect

from vaccination.connectors import InvalidCredentialsException, Authentication
from vaccination.entities import Appointment
from web.views.base import WithService


class AppointmentsView(FlaskView, WithService):

    def index(self):
        try:
            authentication = self._get_auth_from_session()
            if self.service.has_next_appointment(authentication):
                return f'already has an appointment {self.service.current_appointment(authentication)}'
            appointments = self.service.appointments_in_range(authentication, datetime.now().date(), days=30)
            return render_template('appointments.html', appointments=appointments)
        except InvalidCredentialsException:
            return redirect(url_for('HomeView:index'))

    def post(self):
        appointment = Appointment.from_json(request.form)
        try:
            self.service.book_appointment(self._get_auth_from_session(), appointment)
            return f'booked {appointment}'
        except InvalidCredentialsException:
            return redirect(url_for('HomeView:index'))

    def _get_auth_from_session(self):
        if 'auth' not in session:
            raise InvalidCredentialsException()
        authentication = Authentication.from_session(session['auth'])
        return authentication
