from baricadr import create_app, create_celery

application = create_app(config='../local.cfg')
celery = create_celery(application)

if __name__ == '__main__':
    application.run()
