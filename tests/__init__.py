from baricadr import create_app
import pytest


@pytest.fixture
def app():

    current_app = create_app(run_mode='test')

    # Establish an application context before running the tests.
    ctx = current_app.app_context()
    ctx.push()

    return current_app


@pytest.fixture
def client():

    current_app = create_app(run_mode='test')

    # Establish an application context before running the tests.
    ctx = current_app.app_context()
    ctx.push()

    client = current_app.test_client()

    yield client


class BaricadTestCase():
    pass
