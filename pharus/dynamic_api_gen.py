import yaml
from os import path

# Exits the script without killing the python interpreter
def populate_api():
    f = open('pharus//dynamic_api.py', 'w')
    f.write(
"""
from .server import app

@app.route('/test', methods=['GET'])
def test():
    return 'it works!'
"""
    )
    f.close()