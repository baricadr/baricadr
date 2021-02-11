# Baricadr

[![Lint and test](https://github.com/baricadr/baricadr/workflows/Lint%20and%20test/badge.svg)](https://github.com/baricadr/baricadr/actions)

Baricadr is a small application designed to:

- Transfer files from a remote source to a local copy
- Only keep used files in the local copy
- Download data on demand into the local copy

The remote is considered to be a full remote backup of the data (but other use cases are possible).

It is a prototype and not yet ready for production.

It was originally designed for the BBRIC/BARIC CATI at INRA, with the AgroDataRing project.

## Running it with Docker

```
docker-compose build
docker-compose up -d
```

Monitor tasks at http://localhost:5555/

See emails at http://localhost:8025/

## Running tests

Run the app with docker-compose, then run this:

```
docker-compose exec baricadr pytest
```

If you need more details and debug logs:

```
docker-compose exec baricadr pytest -v --log-cli-level debug
```

To run some specific tests:

```
docker-compose exec baricadr pytest -v --log-cli-level debug tests/test_backends.py
docker-compose exec baricadr pytest -v --log-cli-level debug tests/test_backends.py -k test_remote_list_sftp
```

### Running tests on a partition that does not support atime

If you want to run tests on a partition that does not support atime (e.g. mounted with noatime option), you can use a fake ext4 partition supporting atime like this:

```
dd if=/dev/zero of=test-data/test-fs bs=1000 count=1000
mkfs.ext4 test-data/test-fs
sudo mount -o strictatime test-data/test-fs test-data/test-fs-mountpoint
docker-compose -f docker-compose.local-fs.yml up -d
```

When you are done, clean it and unmount it like this:

```
sudo rm -rf test-data/test-fs-mountpoint/*
sudo umount /home/abretaud/git/baricadr/test-data/test-fs-mountpoint
```

## Usage

The best way to use Baricadr is to use the corresponding [python module](https://github.com/baricadr/baricadr_cli) which provides a simple CLI and a python interface.

Baricadr can perform 2 main actions to files:

* Pulling: Baricadr will download some files from the remote source to have them in the local copy
* Freezing: Baricadr will delete local files if they have not been accessed recently, and they are available on the remote source

If you prefer to use it using curl, you can do the following:

### Triggering a "pull"

`curl  -H "Content-type: application/json" -X POST http://localhost:9100/pull -d '{"path": "/some/local/path/test.gz"}'`

### Checking the status

`curl  -H "Content-type: application/json" -X GET http://localhost:9100/status/<pull-id>`

With pull-id = the return of the pull POST call above

## What will it do to my data?

Baricadr will never touch remote data.

When pulling, it will try to respect as much as possible the local data compared to the remote one, which means:

- No risk of multiple pulls at once on the same directory.
  - If one or several subdirs are being pulled, pulling an upper directory will be delayed until subdirs are finished.
  - If a dir is being pulled, no new transfer will be launched when asking to pull a subdir
- When pulling, if a file was modified locally, it will be kept untouched.
- When pulling, if a file was deleted manually locally, it will be downloaded.

We consider that if a local file was modified, it will end up being propagated to the remote during the next backup.

Symlinks are supported as long as they were created on the remote using rclone `--links`.

## Configuring

There are 3 run mode for baricadr: `dev`, `test` and `prod`.

To enable development mode you should set the `BARICADR_RUN_MODE` environment variable to `dev`. It is set by default in the development docker-compose.yml file. Among other things it will display more logs.

This variable can be set to `test` or `prod` values. The default is `prod`.

To override the configuration of the selected run mode, you need to create a file `local.cfg`, by copying `local.example.cfg`. Every config written in this file will override the default one.

You should write a yaml file containing the list of repositories managed by Baricadr. Use this syntax:

```
/some/local/path:
    backend: sftp
    url: sftp.server.fqdn
    user: foo
    password: bar
    exclude: *xml

/another/local/path:
    backend: s3
    url: google
    user: someone
    password: xxxxx
    exclude: *xml
    freezable: True  # Set this to True to allow Baricadr to freeze files (default: False)
    freeze_age: 365   # By default Baricadr will "freeze" files older than 180 days (6 months). You can change this limit with this parameter.
    auto_freeze: True  # Set this to True to schedule regular automated freeze tasks on the whole repo content (default: False)
    auto_freeze_interval: 7  # Delay (in days) between each regular automated freeze task (ignored if auto_freeze is False)
```

You must set the `BARICADR_REPOS_CONF` environment variable to the path to this yaml file, or define it in the `local.cfg` config file. A test one is used by default in the development docker-compose.yml file

## Database

Baricadr uses a small SQL database to store some information.
It uses Flask-migrate to automatically create/update databases. If you modify the models (in `baricadr/db_models.py`), you will need to run the following commands:

```
docker-compose exec baricadr flask db migrate -m "some comment on what you changed"
docker-compose exec baricadr flask db upgrade
```

In testing and development mode, it uses a SQLite database stored in app/data.sqlite
