# -*- coding: utf-8 -*-

DEBUG = True
SECRET_KEY = 'gvrtbtrdgtrgtredsrgvdsvtrhetb486e+rh4d53gv'

from os.path import dirname, abspath, join
SQLALCHEMY_DATABASE_URI = 'sqlite:////%s/data.sqlite' % dirname(abspath(__file__))
SQLALCHEMY_ECHO = True

# make sure that you have started debug mail server using command
# $ make mail
MAIL_SERVER = 'localhost'
MAIL_PORT = 20025
MAIL_USE_SSL = False
MAIL_USERNAME = 'your@email.address'
#MAIL_PASSWORD = 'topsecret'

# Celery
BROKER_TRANSPORT = 'redis'
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_SERIALIZER = 'json'
CELERY_DISABLE_RATE_LIMITS = True
CELERY_ACCEPT_CONTENT = ['json',]
