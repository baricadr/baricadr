# -*- coding: utf-8 -*-

import os
from celery import Celery
from flask import Flask, g, render_template

from .api import api

from .extensions import (celery, db, mail)
from .model import backends
from .model.repos import Repos

__all__ = ('create_app', 'create_celery', )

BLUEPRINTS = (
    api,
)


def create_app(config=None, app_name='baricadr', blueprints=None):
    app = Flask(app_name,
                static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'),
                template_folder="templates"
                )

    configs = {
        "dev": "baricadr.config.DevelopmentConfig",
        "test": "baricadr.config.TestingConfig",
        "prod": "baricadr.config.ProdConfig"
    }
    config_mode = os.getenv('BARICADR_RUN_MODE', 'prod')
    app.config.from_object(configs[config_mode])

    app.config.from_pyfile('../local.cfg', silent=True)
    if config:
        app.config.from_pyfile(config)

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

    # Set info level on logger, which might be overwritten by handers.
    # Suppress DEBUG messages.
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
