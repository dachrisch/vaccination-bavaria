from flask import Flask

from web.views.appointment import AppointmentsView
from web.views.home import HomeView


def add_views(flask_app:Flask):
    HomeView.register(flask_app)
    AppointmentsView.register(flask_app)
