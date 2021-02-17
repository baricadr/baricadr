import os

from baricadr.utils import get_celery_worker_status

from celery import Celery

from flask import Flask, g, render_template

from flask_apscheduler import APScheduler

from .api import api
# Import model classes for flaks migrate
from .db_models import BaricadrTask  # noqa: F401
from .extensions import (celery, db, mail, migrate)
from .model import backends
from .model.repos import Repos


__all__ = ('create_app', 'create_celery', )

BLUEPRINTS = (
    api,
)

CONFIG_KEYS = (
    'SECRET_KEY',
    'BARICADR_REPOS_CONF',
    'MAIL_SENDER',
    'MAIL_ADMIN',
    'CLEANUP_ZOMBIES_INTERVAL',
    'CLEANUP_INTERVAL',
    'CLEANUP_AGE',
    'TASK_LOG_DIR',
    'DEBUG',
    'TESTING',
    'BROKER_TRANSPORT',
    'CELERY_BROKER_URL',
    'CELERY_RESULT_BACKEND',
    'CELERY_TASK_SERIALIZER',
    'CELERY_DISABLE_RATE_LIMITS',
    'CELERY_ACCEPT_CONTENT',
    'SQLALCHEMY_DATABASE_URI',
    'SQLALCHEMY_ECHO',
    'SQLALCHEMY_TRACK_MODIFICATIONS',
    'MAIL_SERVER',
    'MAIL_PORT',
    'MAIL_USE_SSL',
    'MAIL_SENDER',
    'MAIL_SUPPRESS_SEND',
    'LOG_FOLDER',
)


def create_app(config=None, app_name='baricadr', blueprints=None, run_mode=None, is_worker=False):
    app = Flask(app_name,
                static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'),
                template_folder="templates"
                )

    with app.app_context():

        # Can be used to check if some code is executed in a Celery worker, or in the web app
        app.is_worker = is_worker

        configs = {
            "dev": "baricadr.config.DevelopmentConfig",
            "test": "baricadr.config.TestingConfig",
            "prod": "baricadr.config.ProdConfig"
        }
        if run_mode:
            config_mode = run_mode
        else:
            config_mode = os.getenv('BARICADR_RUN_MODE', 'prod')

        if 'BARICADR_RUN_MODE' not in app.config:
            app.config['BARICADR_RUN_MODE'] = config_mode

        app.config.from_object(configs[config_mode])

        app.config.from_pyfile('../local.cfg', silent=True)
        if config:
            app.config.from_pyfile(config)

        app.config = _merge_conf_with_env_vars(app.config)

        # Clean some config values / use default when missing
        if 'CLEANUP_ZOMBIES_INTERVAL' in app.config:
            app.config['CLEANUP_ZOMBIES_INTERVAL'] = _get_int_value(app.config.get('CLEANUP_ZOMBIES_INTERVAL'), 3600)

        if 'CLEANUP_INTERVAL' in app.config:
            app.config['CLEANUP_INTERVAL'] = _get_int_value(app.config.get('CLEANUP_INTERVAL'), 21600)

        if 'TASK_LOG_DIR' in app.config:
            app.config['TASK_LOG_DIR'] = os.path.abspath(app.config['TASK_LOG_DIR'])
        else:
            app.config['TASK_LOG_DIR'] = '/var/log/baricadr/tasks/'

        if 'BARICADR_REPOS_CONF' not in app.config:
            app.config['BARICADR_REPOS_CONF'] = '/etc/baricadr/repos.yml'

        if app.is_worker:
            os.makedirs(app.config['TASK_LOG_DIR'], exist_ok=True)

        # Load the list of baricadr repositories
        app.backends = backends.Backends()
        app.repos = Repos(app.config['BARICADR_REPOS_CONF'], app.backends)

        if blueprints is None:
            blueprints = BLUEPRINTS

        blueprints_fabrics(app, blueprints)
        extensions_fabrics(app)
        configure_logging(app)

        error_pages(app)
        gvars(app)

        # Need to be outside the if, else the worker does not have access to the value
        app.config['CLEANUP_AGE'] = _get_int_value(app.config.get('CLEANUP_AGE'), 365 * 24 * 3600)
        # Moved to not worker, else duplicate tasks (?)
        if not app.is_worker:
            scheduler = APScheduler()
            scheduler.init_app(app)
            scheduler.start()
            if app.config.get("CLEANUP_ZOMBIES_INTERVAL"):
                scheduler.add_job(func=cleanup_zombies, args=[app], trigger='interval', seconds=app.config.get("CLEANUP_ZOMBIES_INTERVAL"), id="cleanup_zombies_job")
            if app.config.get("CLEANUP_INTERVAL"):
                scheduler.add_job(func=cleanup, args=[app], trigger='interval', seconds=app.config.get("CLEANUP_INTERVAL"), id="cleanup_job")
            # Setup freeze job for compatible repos
            setup_freeze_tasks(app, scheduler)

    return app


def create_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask

    app.celery = celery
    return celery


def blueprints_fabrics(app, blueprints):
    """Configure blueprints in views."""

    for blueprint in blueprints:
        app.register_blueprint(blueprint)


def extensions_fabrics(app):
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    celery.config_from_object(app.config)


def error_pages(app):
    # HTTP error pages definitions

    @app.errorhandler(403)
    def forbidden_page(error):
        return render_template("misc/403.html"), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("misc/404.html"), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return render_template("misc/405.html"), 404

    @app.errorhandler(500)
    def server_error_page(error):
        return render_template("misc/500.html"), 500


def gvars(app):
    @app.before_request
    def gdebug():
        if app.debug:
            g.debug = True
        else:
            g.debug = False


def configure_logging(app):
    """Configure file(info) and email(error) logging."""

    if app.debug or app.testing:
        # Skip debug and test mode. Just check standard output.
        return

    import logging
    from logging.handlers import SMTPHandler

    # Set log level
    if app.config['BARICADR_RUN_MODE'] == 'test':
        app.logger.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.INFO)

    info_log = os.path.join(app.config['LOG_FOLDER'], 'info.log')
    info_file_handler = logging.handlers.RotatingFileHandler(info_log, maxBytes=100000, backupCount=10)
    info_file_handler.setLevel(logging.INFO)
    info_file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')
    )
    app.logger.addHandler(info_file_handler)

    credentials = None
    if 'MAIL_USERNAME' in app.config and 'MAIL_PASSWORD' in app.config:
        credentials = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
    mailhost = app.config['MAIL_SERVER']
    if 'MAIL_PORT' in app.config:
        mailhost = (app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
    mail_handler = SMTPHandler(mailhost,
                               app.config['MAIL_SENDER'],
                               app.config['MAIL_ADMIN'],
                               'BARICADR failed!',
                               credentials)
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')
    )
    app.logger.addHandler(mail_handler)


def setup_freeze_tasks(app, scheduler):
    with app.app_context():

        for path, repo in app.repos.repos.items():
            if not repo.freezable or not repo.auto_freeze:
                continue

            app.logger.debug("Creating scheduler job for path : %s with auto_freeze_interval : %s" % (path, repo.auto_freeze_interval))
            scheduler.add_job(func=freeze_repo, args=[app, path], trigger='interval', days=repo.auto_freeze_interval, id="auto_freeze_%s" % (path), name="Auto freeze job for path %s" % (path))


def freeze_repo(app, repo_path):

    celery_status = get_celery_worker_status(app.celery)
    if celery_status['availability'] is None:
        app.logger.error("Trying to schedule an auto freeze task on repo '%s', but no Celery worker available to process the request. Aborting.", repo_path)
        return

    admin_email = app.config.get('MAIL_ADMIN', None)
    admin_email.split(',')

    touching_task_id = app.repos.is_already_touching(repo_path)
    if not touching_task_id:
        locking_task_id = app.repos.is_locked_by_subdir(repo_path)
        task = app.celery.send_task('freeze', (repo_path, admin_email, locking_task_id))
        task_id = task.task_id

        pt = BaricadrTask(path=repo_path, type='freeze', task_id=task_id)
        db.session.add(pt)
        db.session.commit()


def cleanup(app):
    app.celery.send_task('cleanup_tasks', (app.config['CLEANUP_AGE'],))


def cleanup_zombies(app):
    app.celery.send_task('cleanup_zombie_tasks')


def _get_int_value(config_val, default):
    if not config_val:
        config_val = default
    try:
        config_val = int(config_val)
    except ValueError:
        config_val = default
    return config_val


def _merge_conf_with_env_vars(config):

    for key in CONFIG_KEYS:
        envval = os.getenv(key)
        if envval is not None:
            config[key] = envval

    return config
