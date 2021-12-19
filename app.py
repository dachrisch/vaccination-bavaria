import logging
from logging import basicConfig
from logging import getLogger

from vaccination.connectors import ImpzentrenBayernConnector
from web import create_app


def run_flask():
    app = create_app()
    basicConfig(level=logging.INFO)
    getLogger(ImpzentrenBayernConnector.__name__).setLevel(logging.DEBUG)
    app.run(debug=True, ssl_context='adhoc')


def run_waitress(*args,**kwargs):
    app = create_app()

    basicConfig(level=logging.INFO)
    getLogger(ImpzentrenBayernConnector.__name__).setLevel(logging.DEBUG)
    return app


if __name__ == '__main__':
    run_flask()
