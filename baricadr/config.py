class BaseConfig(object):
    DEBUG = False
    TESTING = False

    BARICADR_VERSION = "0.1.1"

    # Celery
    BROKER_TRANSPORT = 'redis'
    CELERY_BROKER_URL = 'redis://redis:6379/0'
    CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_DISABLE_RATE_LIMITS = True
    CELERY_ACCEPT_CONTENT = ['json', ]

    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    LOG_FOLDER = "/var/log/baricadr/"


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = True

    MAIL_SERVER = 'mailhog'
    MAIL_PORT = 1025
    MAIL_USE_SSL = False
    MAIL_SENDER = 'your@email.address'
    MAIL_SUPPRESS_SEND = False  # enabling TESTING above sets this one to True, which we don't want as we use mailhog

    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@db/postgres'
    SQLALCHEMY_ECHO = True


class TestingConfig(BaseConfig):
    DEBUG = False
    TESTING = True

    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@db/postgres'
    SQLALCHEMY_ECHO = False


class ProdConfig(BaseConfig):
    DEBUG = False
    TESTING = False

    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@db/postgres'
    SQLALCHEMY_ECHO = False
