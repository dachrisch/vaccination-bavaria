import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from web.views import add_views


def create_app():
    flask_app = Flask(__name__, template_folder='../templates')

    flask_app.wsgi_app = ProxyFix(flask_app.wsgi_app)

    flask_app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))

    add_views(flask_app)

    return flask_app
