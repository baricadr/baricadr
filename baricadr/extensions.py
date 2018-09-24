# -*- coding: utf-8 -*-

from flask_mail import Mail
mail = Mail()

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from celery import Celery
celery = Celery()
