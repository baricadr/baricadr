# -*- coding: utf-8 -*-

from celery.result import AsyncResult
from flask import (Blueprint, current_app, jsonify, request)

api = Blueprint('api', __name__, url_prefix='/')


@api.route('/pull', methods=['POST'])
def pull_files():
    current_app.logger.info(request.json)
    celery = current_app.celery
    # TODO check that 'files' exists
    task = celery.send_task('pull_file', (request.json['files'],))
    return jsonify({'tasks': task.task_id})


@api.route('/status/<task_id>', methods=['GET'])
def status_pull(task_id):
    current_app.logger.info("Getting status of task_id")
    res = AsyncResult(task_id)
    return jsonify({'finished': res.ready(), 'info': res.info})
