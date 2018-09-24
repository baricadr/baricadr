from baricadr import create_app

application = create_app(config='../local.cfg')

if __name__ == '__main__':
    application.run()
