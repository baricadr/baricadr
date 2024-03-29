import os

from baricadr.db_models import BaricadrTask
from baricadr.extensions import db
from baricadr.utils import get_celery_worker_status

from celery.result import AsyncResult

from email_validator import EmailNotValidError, validate_email

from flask import (Blueprint, current_app, jsonify, make_response, request)


api = Blueprint('api', __name__, url_prefix='/')


# Global error handler
@api.errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, RuntimeError):
        return jsonify({'error': str(e)}), 400

    # now you're handling non-HTTP exceptions only
    return jsonify({'error': 'Internal server error'}), 502


# Endpoint to check if API is running for CLI tests
@api.route('/version', methods=['GET'])
def version():
    return jsonify({"version": current_app.config.get("BARICADR_VERSION", "unknown")})


# Might return arguments?
@api.route('/endpoints', methods=['GET'])
def endpoints():
    endpoints = {}
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        endpoints[rule.endpoint.split(".")[-1]] = rule.rule
    return jsonify(endpoints)


@api.route('/pull', methods=['POST'])
def pull():
    current_app.logger.debug("API call: Pulling %s" % request.json)

    return __pull_or_freeze('pull', request)


@api.route('/freeze', methods=['POST'])
def freeze():
    current_app.logger.debug("API call: Freezing %s" % request.json)

    return __pull_or_freeze('freeze', request)


@api.route('/list', methods=['POST'])
def list():
    current_app.logger.debug("API call: Listing %s" % request.json)

    if not request.json or 'path' not in request.json:
        return jsonify({'error': 'Missing "path"'}), 400

    missing = False
    from_root = False
    full = False

    if 'missing' in request.json and str(request.json['missing']).lower() == "true":
        missing = True

    if 'full' in request.json and str(request.json['full']).lower() == "true":
        full = True

    max_depth = 1
    if 'max_depth' in request.json:
        if request.json['max_depth']:
            max_depth = request.json['max_depth']
        else:
            max_depth = 0

    if 'from_root' in request.json and str(request.json['from_root']).lower() == "true":
        from_root = request.json['from_root']

    asked_path = os.path.abspath(request.json['path'])
    repo = current_app.repos.get_repo(asked_path)
    files = repo.remote_list(asked_path, missing=missing, max_depth=max_depth, from_root=from_root, full=full)

    return jsonify(files)


@api.route('/tree', methods=['POST'])
def tree():
    current_app.logger.debug("API call: Tree listing %s" % request.json)

    if not request.json or 'path' not in request.json:
        return jsonify({'error': 'Missing "path"'}), 400

    max_depth = 1
    if 'max_depth' in request.json:
        if request.json['max_depth']:
            max_depth = request.json['max_depth']
        else:
            max_depth = 0

    asked_path = os.path.abspath(request.json['path'])
    repo = current_app.repos.get_repo(asked_path)
    files = repo.remote_tree(asked_path, max_depth=max_depth)

    return jsonify(files)


def __pull_or_freeze(action, request):

    if action not in ['pull', 'freeze']:
        raise RuntimeError('Unexpected action %s' % action)

    if 'path' not in request.json:
        return jsonify({'error': 'Missing "path"'}), 400

    # Normalize path
    asked_path = os.path.abspath(request.json['path'])

    celery_status = get_celery_worker_status(current_app.celery)
    if celery_status['availability'] is None:
        current_app.logger.error("Received '%s' action on path '%s', but no Celery worker available to process the request. Aborting." % (action, asked_path))
        return jsonify({'error': 'No Celery worker available to process the request'}), 400

    email = None
    if 'email' in request.json and request.json['email']:
        email = request.json['email']

        try:
            v = validate_email(email)
            email = [v["email"]]
        except EmailNotValidError as e:
            return jsonify({'error': str(e)}), 400

    dry_run = False
    if 'dry_run' in request.json:
        dry_run = str(request.json['dry_run']).lower() in ["true", "1", "yes"]

    # Check if we're already touching the path
    touching_task_id = current_app.repos.is_already_touching(asked_path)
    if touching_task_id:
        current_app.logger.info("Already touching this path '%s' in task '%s', no new task." % (asked_path, touching_task_id))
        task_id = touching_task_id
    else:
        locking_task_id = current_app.repos.is_locked_by_subdir(asked_path)

        task = current_app.celery.send_task(action, (asked_path, email, locking_task_id, dry_run))
        task_id = task.task_id
        current_app.logger.info("Created %s task %s" % (action, task_id))

        # Save a reference to this task in db
        pt = BaricadrTask(path=asked_path, type=action, task_id=task_id)
        db.session.add(pt)
        db.session.commit()

    return jsonify({'task': task_id})


@api.route('/tasks', methods=['GET'])
def task_list():
    current_app.logger.info("API call: Getting list of tasks")

    tasks_json = []

    running_tasks = BaricadrTask.query.all()
    for rt in running_tasks:
        tasks_json.append({
            'task_id': rt.task_id,
            'type': rt.type,
            'path': rt.path,
            'status': rt.status,
            'created': rt.created,
            'started': rt.started,
            'finished': rt.finished
        })

    return jsonify(tasks_json)


@api.route('/tasks/status/<task_id>', methods=['GET'])
def task_show(task_id):
    current_app.logger.info("API call: Getting status of task %s" % task_id)

    status = {}

    # Get status from db (if still there)
    db_task = BaricadrTask.query.filter_by(task_id=task_id)
    if db_task.count():
        db_task = db_task.one()
        status = {
            'path': db_task.path,
            'type': db_task.type,
            'task_id': db_task.task_id,
            'status': db_task.status,
            'created': db_task.created,
            'started': db_task.started,
            'finished': db_task.finished,
            'error': db_task.error
        }
        code = 200
    else:
        status = {'error': 'Task not found in Baricadr database. Maybe it is too old.'}
        code = 404

    current_app.logger.debug("Task state from database: %s" % status)
    return make_response(jsonify(status), code)


@api.route('/tasks/log/<task_id>', methods=['GET'])
def task_log(task_id):
    current_app.logger.info("API call: Getting logs of task %s" % task_id)

    status = {}

    # Get status from db (if still there)
    db_task = BaricadrTask.query.filter_by(task_id=task_id)
    if db_task.count():
        db_task = db_task.one()
        logfile = db_task.logfile_path(current_app, task_id)

        if not os.path.exists(logfile) or not os.path.isfile(logfile):
            status = {'error': 'Task log not found, maybe it is too old.'}
            code = 404
        else:
            with open(logfile, 'r') as logfileh:
                status = {
                    'logs': logfileh.read(),
                }
            code = 200
    else:
        status = {'error': 'Task not found in Baricadr database. Maybe it is too old.'}
        code = 404

    return make_response(jsonify(status), code)


@api.route('/tasks/remove/<task_id>', methods=['GET'])
def task_remove(task_id):
    current_app.logger.info("API call: Killing task %s" % task_id)
    status = {
        'info': "",
        'error': ""
    }
    # Get task from DB
    db_task = BaricadrTask.query.filter_by(task_id=task_id)
    if db_task.count():
        db_task = db_task.one()
        if db_task.status in ['started', 'waiting']:
            AsyncResult(task_id).revoke(terminate=True)

        db.session.delete(db_task)
        db.session.commit()
        status['info'] = "Task %s removed." % (task_id)
        code = 200

    else:
        status['error'] = 'Task not found in Baricadr database.'
        code = 404

    return make_response(jsonify(status), code)


@api.route('/zombie', methods=['GET'])
def zombie():
    current_app.logger.info("API call: Killing zombies")

    celery_status = get_celery_worker_status(current_app.celery)
    if celery_status['availability'] is None:
        current_app.logger.error("Received 'zombie' action, but no Celery worker available to process the request. Aborting.")
        return jsonify({'error': 'No Celery worker available to process the request'}), 400

    task = current_app.celery.send_task('cleanup_zombie_tasks')
    task_id = task.task_id
    return jsonify({'task': task_id})
