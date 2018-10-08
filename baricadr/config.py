from os.path import abspath, dirname


class BaseConfig(object):
    DEBUG = False
    TESTING = False

    # Celery
    BROKER_TRANSPORT = 'redis'
    CELERY_BROKER_URL = 'redis://redis:6379/0'
    CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_DISABLE_RATE_LIMITS = True
    CELERY_ACCEPT_CONTENT = ['json', ]

    SQLALCHEMY_ECHO = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = True

    MAIL_SERVER = 'mailhog'
    MAIL_PORT = 1025
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'your@email.address'
    MAIL_SUPPRESS_SEND = False  # enabling TESTING above sets this one to True, which we don't want as we use mailhog

    SQLALCHEMY_DATABASE_URI = 'sqlite:////%s/data.sqlite' % dirname(abspath(__file__))
    SQLALCHEMY_ECHO = True


class TestingConfig(BaseConfig):
    DEBUG = False
    TESTING = True

    SQLALCHEMY_DATABASE_URI = 'sqlite:////%s/data.sqlite' % dirname(abspath(__file__))
    SQLALCHEMY_ECHO = True


class ProdConfig(BaseConfig):
    DEBUG = False
    TESTING = False
