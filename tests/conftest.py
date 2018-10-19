from baricadr.app import create_app, create_celery

import pytest


@pytest.fixture
def app():

    current_app = create_app(run_mode='test')
    create_celery(current_app)

    # Establish an application context before running the tests.
    ctx = current_app.app_context()
    ctx.push()

    return current_app


@pytest.fixture
def client():

    current_app = create_app(run_mode='test')
    create_celery(current_app)

    # Establish an application context before running the tests.
    ctx = current_app.app_context()
    ctx.push()

    client = current_app.test_client()

    yield client
