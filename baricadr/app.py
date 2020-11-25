import os

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

        app.config['MAX_TASK_DURATION'] = _get_int_value(app.config.get('MAX_TASK_DURATION'), 21600)

        if 'CLEANUP_ZOMBIES_INTERVAL' in app.config:
            app.config['CLEANUP_ZOMBIES_INTERVAL'] = _get_int_value(app.config.get('CLEANUP_ZOMBIES_INTERVAL'), 3600)
        if 'CLEANUP_INTERVAL' in app.config:
            app.config['CLEANUP_INTERVAL'] = _get_int_value(app.config.get('CLEANUP_INTERVAL'), 21600)
        if 'FREEZE_INTERVAL' in app.config:
            app.config['FREEZE_INTERVAL'] = _get_int_value(app.config.get('FREEZE_INTERVAL'), 86400)

        # Load the list of baricadr repositories
        app.backends = backends.Backends()
        if 'BARICADR_REPOS_CONF' in app.config:
            repos_file = app.config['BARICADR_REPOS_CONF']
        else:
            repos_file = os.getenv('BARICADR_REPOS_CONF', '/etc/baricadr/repos.yml')
        app.repos = Repos(repos_file, app.backends)

        if blueprints is None:
            blueprints = BLUEPRINTS

        blueprints_fabrics(app, blueprints)
        extensions_fabrics(app)
        configure_logging(app)

        error_pages(app)
        gvars(app)

        # Should it be on the worker?
        if app.is_worker:
            scheduler = APScheduler()
            scheduler.init_app(app)
            scheduler.start()
            if app.config.get("CLEANUP_ZOMBIES_INTERVAL"):
                scheduler.add_job(func=cleanup_zombies, args=[app], trigger='interval', seconds=app.config.get("CLEANUP_ZOMBIES_INTERVAL"), id="cleanup_zombies_job")
            if app.config.get("CLEANUP_INTERVAL"):
                scheduler.add_job(func=cleanup, args=[app], trigger='interval', seconds=app.config.get("CLEANUP_INTERVAL"), id="cleanup_job")
            if app.config.get("FREEZE_INTERVAL"):
                scheduler.add_job(func=freeze_repos, args=[app], trigger='interval', seconds=app.config.get("FREEZE_INTERVAL"), id="freeze_job")

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

    # Testing
    # app.logger.info("testing info.")
    # app.logger.warn("testing warn.")
    # app.logger.error("testing error.")

    mail_handler = SMTPHandler(app.config['MAIL_SERVER'],
                               app.config['MAIL_USERNAME'],
                               app.config['ADMINS'],
                               'O_ops... %s failed!' % app.config['PROJECT'],
                               (app.config['MAIL_USERNAME'],
                                app.config['MAIL_PASSWORD']))
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')
    )
    app.logger.addHandler(mail_handler)


def freeze_repos(app):

    for path, repo in app.repos.items():
        if not repo.freezable:
            continue

        touching_task_id = app.repos.is_already_touching(path)
        if not touching_task_id:
            locking_task_id = app.repos.is_locked_by_subdir(path)

            task = app.celery.send_task('freeze', (path, None, locking_task_id))
            task_id = task.task_id

            pt = BaricadrTask(path=path, type='freeze', task_id=task_id)
            db.session.add(pt)
            db.session.commit()


def cleanup(app):
    app.celery.send_task('cleanup_tasks')


def cleanup_zombies(app):
    app.celery.send_task('cleanup_zombies_tasks')


def _get_int_value(config_val, default):
    try:
        config_val = int(config_val)
    except ValueError:
        config_val = default
    return config_val
