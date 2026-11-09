import datetime

from flask import jsonify

API_NAME = 'Task Manager API'
API_VERSION = '1.0'


class SystemController:
    def index(self):
        return jsonify({'message': API_NAME, 'version': API_VERSION})

    def health(self):
        return jsonify({'status': 'ok', 'timestamp': str(datetime.datetime.now())})
