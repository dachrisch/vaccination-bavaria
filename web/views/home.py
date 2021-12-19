from flask import render_template, url_for, request, session
from flask_classful import FlaskView
from werkzeug.utils import redirect

from vaccination.connectors import InvalidCredentialsException
from vaccination.login import UsernamePasswordLoginProvider
from web.views.base import WithService


class HomeView(FlaskView, WithService):
    route_base = '/'

    def __init__(self):
        super().__init__()
        self.login_provider = UsernamePasswordLoginProvider()

    def post(self):
        username = request.form['username']
        password = request.form['password']
        self.login_provider.provide(username, password)
        try:
            authentication = self.service.authentication(self.login_provider)
            session['auth'] = authentication.access_token
            return redirect(url_for('AppointmentsView:index'))
        except InvalidCredentialsException:
            return render_template('home.html', error='invalid credentials')

    def index(self):
        return render_template('home.html')
