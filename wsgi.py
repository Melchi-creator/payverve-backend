"""
wsgi.py

web server gateway interface
Application Entry Point in Production
"""

import config
from .server import server as payverve

if __name__ == '__main__':
    if config.env == 'prod':
        payverve.run()
