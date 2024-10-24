#!/bin/bash

clear

export flask_app="src/server.py"

export flask_debug=true

python -m src.server
