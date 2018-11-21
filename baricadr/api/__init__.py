import os

from baricadr.db_models import PullTask

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

    # Normalize path
    asked_path = os.path.abspath(request.json['path'])

    email = None
    if 'email' in request.json:
        email = request.json['email']

        try:
            v = validate_email(email)
            email = v["email"]
        except EmailNotValidError as e:
            return jsonify({'error': str(e)}), 400

    if 'path' not in request.json:
        return jsonify({'error': 'Missing "path"'}), 400

    # Check if we're already pulling the file
    pulling_task_id = current_app.repos.is_pulling(asked_path)
    if pulling_task_id:
        current_app.logger.info("Already pulling '%s' in task '%s', no new task." % (asked_path, pulling_task_id))
        task_id = pulling_task_id
    else:
        task = celery.send_task('pull_file', (asked_path, email))
        task_id = task.task_id

        # Save a reference to this task in db
        pt = PullTask(path=asked_path, task_id=task_id)
        current_app.db.session.add(pt)
        current_app.db.session.commit()

    return jsonify({'tasks': task_id})


@api.route('/status/<task_id>', methods=['GET'])
def status_pull(task_id):
    current_app.logger.info("Getting status of task_id")
    res = AsyncResult(task_id)
    info = res.info
    error = 'false'

    # Make exceptions readable
    if isinstance(info, RuntimeError):
        error = 'true'
        info = str(info)

    current_app.logger.debug("Task state from Celery: %s" % res.info)
    return jsonify({'finished': str(res.ready()).lower(), 'error': error, 'info': info})
