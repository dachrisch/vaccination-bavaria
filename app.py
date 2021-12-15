import logging
from logging import basicConfig
from logging import getLogger
from flask import url_for
from flask_bootstrap import bootstrap_find_resource, WebCDN, StaticCDN, ConditionalCDN

from connectors import ImpzentrenBayerConnector
from web import create_app


def run_flask():
    app = create_app()
    basicConfig(level=logging.INFO)
    getLogger(ImpzentrenBayerConnector.__name__).setLevel(logging.DEBUG)
    app.run(debug=True, ssl_context='adhoc')


if __name__ == '__main__':
    run_flask()
