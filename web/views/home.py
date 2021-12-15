from datetime import datetime

from flask import render_template, url_for, request
from flask_classful import FlaskView
from werkzeug.utils import redirect

from connectors import ImpzentrenBayerConnector, UsernamePasswordLoginProvider, InvalidCredentialsException
from web.views.base import WithConnector


class HomeView(FlaskView, WithConnector):
    route_base = '/'

    def post(self):
        username = request.form['username']
        password = request.form['password']
        self.connector.login_provider.provide(username, password)
        try:
            self.connector.authenticate_session()
            return redirect(url_for('AppointmentsView:index'))
        except InvalidCredentialsException:
            return render_template('home.html', error='invalid credentials')

    def index(self):
        return render_template('home.html')
