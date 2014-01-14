""" main.py is the top level script.
"""

from flask import Flask
import settings

app = Flask(__name__.split('.')[0])
app.config.from_object(settings)

import urls