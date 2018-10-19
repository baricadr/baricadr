# -*- coding: utf-8 -*-

from celery.result import AsyncResult
from email_validator import EmailNotValidError, validate_email
from flask import (Blueprint, current_app, jsonify, request)

api = Blueprint('api', __name__, url_prefix='/')


@api.route('/pull', methods=['POST'])
def pull_files():
    current_app.logger.debug("API call pull: %s" % request.json)
    celery = current_app.celery

    if 'path' not in request.json:
        return jsonify({'error': 'Missing "path"'}), 400

    # TODO normalize path

    # TODO check email is valid
    email = None
    if 'email' in request.json:
        email = request.json['email']

        try:
            v = validate_email(email)
            email = v["email"]
        except EmailNotValidError as e:
            return jsonify({'error': str(e)}), 400

    task = celery.send_task('pull_file', (request.json['path'], email))

    return jsonify({'tasks': task.task_id})


@api.route('/status/<task_id>', methods=['GET'])
def status_pull(task_id):
    current_app.logger.info("Getting status of task_id")
    res = AsyncResult(task_id)
    return jsonify({'finished': res.ready(), 'info': res.info})
