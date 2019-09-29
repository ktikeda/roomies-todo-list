from flask import jsonify
from roomies_todo_list import app
from .models import BadRequest

@app.errorhandler(BadRequest)
def handle_bad_request(error):
    """Catch BadRequest exception globally, serialize into JSON, and respond with 400."""
    body = {'error': dict(error.payload or ())}
    body['error']['message'] = error.message
    return jsonify(body), error.status

