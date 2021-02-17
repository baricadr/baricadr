# Baricadr

[![Lint and test](https://github.com/baricadr/baricadr/workflows/Lint%20and%20test/badge.svg)](https://github.com/baricadr/baricadr/actions)
[![Docker Repository on Quay](https://quay.io/repository/baricadr/baricadr/status "Docker Repository on Quay")](https://quay.io/repository/baricadr/baricadr)
[![Docker Repository on Quay](https://quay.io/repository/baricadr/baricadr-worker/status "Docker Repository on Quay")](https://quay.io/repository/baricadr/baricadr-worker)

Baricadr is a small application allowing to transfer data between two mirrored data repositories: one local, and one on a remote server. The remote one is usually a backup of the local one.

The aim of Baricadr is to save local disk space, by keeping in the local repository **only** the files that are really used ("hot data"), and to remove files that have not been accessed for a (configurable) while ("cold data").

Baricadr uses [Rclone](https://rclone.org/) for data transfers. Currently, the remote server must be accessible using SFTP, but other methods should be easy to implement (in particular the ones that Rclone is able to use).

Two main actions can be performed with Baricadr:

- Freeze local files: remove unused files from the local copy
- Pull remote files: download data from the remote server into the local copy

One can also use Baricadr in Pull-mode only, allowing to download easily selected files from a remote server.

Although we did our best to make Baricadr as safe as possible for your data, there can always remain bugs, and it can be dangerous if not configured properly. **Use at your own risk**.

Baricadr was originally designed for the [BARIC CATI](https://www.cesgo.org/catibaric/) at INRAE, with the [AgroDataRing](https://datapartage.inrae.fr/Gerer/Stocker-les-donnees/AgroDataRing) project.

## Usage

Baricadr runs as a web service, exposing a very simple REST API.

The easiest way to use Baricadr is to use the corresponding [python module](https://github.com/baricadr/barique) which provides a simple CLI (`barique`) and a python interface to interact with the REST API.

Baricadr can perform 2 main actions to files:

* Pulling: Baricadr will download some files from the remote source to have them in the local copy
* Freezing: Baricadr will delete local files if they have not been accessed recently, and they are available on the remote source

Install and initialize the module:

```bash
$ pip install barique

# On first use you'll need to create a config file to connect to the server, just run:

$ barique init
Welcome to Barique
Baricadr server host: localhost
Baricadr server port: 9100
Is your Baricadr instance running behind an authentication proxy? [y/N]: n
Testing connection...
Ok! Everything looks good.
Ready to go! Type `barique` to get a list of commands you can execute.

```

Ask Baricadr to pull a single file (you can pull/freeze whole dirs too):

```bash
$ barique file pull /repos/test_repo/file.txt
7958b29c-2a14-486c-90f0-585e68ac9f44

# Check the status of a pull task
$ barique task show 7958b29c-2a14-486c-90f0-585e68ac9f44
{
    "created": "Wed, 17 Feb 2021 15:11:56 GMT",
    "error": null,
    "finished": "Wed, 17 Feb 2021 15:12:03 GMT",
    "path": "/repos/test_repo/file.txt",
    "started": "Wed, 17 Feb 2021 15:11:58 GMT",
    "status": "finished",
    "task_id": "7958b29c-2a14-486c-90f0-585e68ac9f44",
    "type": "pull"
}
```

Ask Baricadr to freeze a single file:

```bash
$ barique file freeze /repos/test_repo/file2.txt
7958b29c-2a14-486c-90f0-585e68ac9f44

# Check the status of a pull task
$ barique task show 7958b29c-2a14-486c-90f0-585e68ac9f44
{
    "created": "Wed, 17 Feb 2021 15:16:49 GMT",
    "error": null,
    "finished": "Wed, 17 Feb 2021 15:16:52 GMT",
    "path": "/repos/test_repo/file2.txt",
    "started": "Wed, 17 Feb 2021 15:16:51 GMT",
    "status": "finished",
    "task_id": "7958b29c-2a14-486c-90f0-585e68ac9f44",
    "type": "freeze"
}
```

### Using Curl

If you prefer to use Baricadr using curl, you can run things like the following:

### Triggering a "pull"

`curl -H "Content-type: application/json" -X POST http://localhost:9100/pull -d '{"path": "/some/local/path/test.gz"}'`

### Checking the status

`curl -H "Content-type: application/json" -X GET http://localhost:9100/tasks/status/<pull-id>`

With pull-id = the return of the pull POST call above

## What will it do to my data?

Baricadr will never touch remote data. We consider that remote data is a backup, and that it is **safe** (ideally replicated elsewhere and regularly tested).

To allow freezing, Baricadr needs (and will refuse to work without) support for file access time (atime) on the partition containing the data to manage. You can still use the pull mechanism of Baricadr if atime is not supported.

When pulling, it will try to respect as much as possible the local data compared to the remote one, which means:

- No risk of multiple pulls at once on the same directory.
  - If one or several subdirs are being pulled, pulling an upper directory will be delayed until subdirs are finished.
  - If a dir is being pulled, no new transfer will be launched when asking to pull a subdir
- When pulling, if a file was modified locally, it will be kept untouched.
- When pulling, if a file was deleted manually locally, it will be downloaded.

We consider that if a local file was modified, it will end up being propagated to the remote during the next backup.

Symlinks are supported as long as they were created on the remote using rclone `--links`.

### How to backup data to the remote

Baricadr consider that new data is regularly sent to the remote using Rclone, with a command like that:

```bash
rclone sync --progress --verbose --links --config /some/rclone.conf /local/repo/ remote-server:/remote/repo/ --sftp-user "someone" --sftp-pass "yourpassword"
```

The most important is to **NOT** use the `--delete-*` options of `rclone`: if you'd use it and perform some Freeze operations, the files deleted locally would be deleted also on the remote during the next backup, and **YOU DON'T WANT THAT** (trust me).

It might be possible to perform backups with other tools like `rsync`, but it could cause problems in particular with symlinks.

## Running it with Docker

Check configuration (see below), then:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

Alternatively, you can run a development version to test things:

```bash
docker-compose -f docker-compose.dev.yml up -d
```

Monitor tasks at http://localhost:5555/

See emails at http://localhost:8025/

## Configuring

### Application configuration

Baricadr main configuration is written in a single config file that Baricadr expects to find at `/baricadr/local.cfg` inside the container. A template for this file is available in [local.example.cfg](./local.example.cfg). You are supposed to create your own `local.cfg` file based on the template, and mount it to `/baricadr/local.cfg`.

All configuration options can also be overriden using environment variables (same names as in `local.cfg`).

Don't forget to set the `SECRET_KEYS` option to a random value for security (and keep it private).

#### Run modes

There are 3 run mode for baricadr: `dev`, `test` and `prod`.

To enable development mode you should set the `BARICADR_RUN_MODE` environment variable to `dev`. It is set by default in the development `docker-compose.dev.yml` file. Among other things it will display more logs and perform live reload of modified code.

This variable can also be set to `test` or `prod` values. The default is `prod`.

To override the configuration of the selected run mode, you need to create a file `local.cfg`, by copying `local.example.cfg`. Every config written in this file will override the default one.

### Repositories configuration

You need to write a yaml file containing the list of repositories that you wish to be managed by Baricadr. Use this syntax:

```yaml
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
    chown_uid: 9876  # When pulling files, change owner to specified user id (default: the user running baricadr, root)
    chown_gid: 9876  # When pulling files, change owner to specified group id (default: the user running baricadr, root)
```

You must set the `BARICADR_REPOS_CONF` environment variable to the path to this yaml file, or define it in the `local.cfg` config file. A test one is used by default in the development `docker-compose.dev.yml` file

## Database

Baricadr uses a small SQL database to store some information.
It uses Flask-migrate to automatically create/update databases. If you modify the models (in `baricadr/db_models.py`), you will need to run the following commands:

```bash
docker-compose exec baricadr flask db migrate -m "some comment on what you changed"
docker-compose exec baricadr flask db upgrade
```

In testing and development mode, it uses a SQLite database stored in app/data.sqlite

## Authentication

**No** authentication mechanism is implemented in Baricadr. To restrict usage, you can run Baricadr behind a reverse proxy that will take care of authentication.

You can for example run Baricadr behind an Nginx (or Apache) reverse proxy, configured to use LDAP authentication, or a simple HTTP Basic auth.

Look at [docker-compose.local-fs-auth.yml](./docker-compose.local-fs-auth.yml) for an example of such a system where the Baricadr API is restricted to a `baricadr` user (password: `baricadr`).

Commands used to generate the [htpasswd_user](./docker/htpasswd_user) file:

```bash
echo -n 'baricadr:' >> ./docker/htpasswd_user
openssl passwd -apr1 >> ./docker/htpasswd_user
```

## Running tests

Run the app with docker-compose, then run this:

```bash
docker-compose -f docker-compose.dev.yml exec baricadr pytest
```

If you need more details and debug logs:

```bash
docker-compose -f docker-compose.dev.yml exec baricadr pytest -v --log-cli-level debug
```

To run some specific tests:

```bash
docker-compose -f docker-compose.dev.yml exec baricadr pytest -v --log-cli-level debug tests/test_backends.py
docker-compose -f docker-compose.dev.yml exec baricadr pytest -v --log-cli-level debug tests/test_backends.py -k test_remote_list_sftp
```

### Running tests on a partition that does not support atime

If you want to run tests on a partition that does not support atime (e.g. mounted with noatime option), you can use a fake ext4 partition supporting atime like this:

```bash
dd if=/dev/zero of=test-data/test-fs bs=1000 count=1000
mkfs.ext4 test-data/test-fs
sudo mount -o strictatime test-data/test-fs test-data/test-fs-mountpoint
docker-compose -f docker-compose.local-fs.yml up -d
```

When you are done, clean it and unmount it like this:

```bash
sudo rm -rf test-data/test-fs-mountpoint/*
sudo umount /home/abretaud/git/baricadr/test-data/test-fs-mountpoint
```

## License

Available under the MIT License
