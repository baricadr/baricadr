all: setup

venv/bin/activate:
	virtualenv venv

run: venv/bin/activate requirements.txt
	. venv/bin/activate; uwsgi --socket 0.0.0.0:5000 --protocol=http -w app

dev: venv/bin/activate requirements.txt
	. venv/bin/activate; uwsgi --py-autoreload 1 --socket 0.0.0.0:5000 --protocol=http -w app

setup: venv/bin/activate requirements.txt
	. venv/bin/activate; pip install -Ur requirements.txt

celery:
	. venv/bin/activate; python celery.py worker

# celery in debug state
dcelery:
	. venv/bin/activate; python celery.py worker -l info --autoreload
