import yaml
from os import path

# Exits the script without killing the python interpreter
def populate_api():
    
    f = open('pharus//dynamic_api.py', 'w')
    y = open('pharus//dynamic_api_spec.yaml', 'r')
    
    valuesYaml = yaml.load(y, Loader=yaml.FullLoader)
    f.write(
"""
from .server import app

@app.route('/test', methods=['GET'])
def test():

    return '{field}'
""".format(field=valuesYaml['Test'])
    )
    f.close()