"""wsgi.py

web server gateway interface
"""

from . import config
from .server import server as payverve

if __name__ == '__main__':
    if config.env == 'prod':
        payverve.run()
