BARICADR is a small application designed to:

- Transfer files from a remote source to a local copy
- Only keep used files in the local copy
- Download data on demand into the local copy

It is a prototype and not yet ready for production.

It was originally designed for the BBRIC/BARIC CATI at INRA, with the AgroDataRing project.

# Running it with Docker

```
docker-compose build
docker-compose up -d
```

Monitor tasks at http://localhost:5555/
See emails at http://localhost:8025/

# Running tests

Run the app with docker-compose, then run this:

```
docker-compose exec baricadr pytest
```

If you need more details and debug logs:

```
docker-compose exec baricadr pytest -v --log-cli-level debug
```

# Using it

## Triggering a "pull"

`curl  -H "Content-type: application/json" -X POST http://localhost:9100/pull -d '{"path": "/some/local/path/test.gz"}'`

## Checking the status

`curl  -H "Content-type: application/json" -X GET http://localhost:9100/status/<pull-id>`

With pull-id = the return of the pull POST call above

# Configuring

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
```

You must set the `BARICADR_REPOS_CONF` environment variable to the path to this yaml file, or define it in the `local.cfg` config file. A test one is used by default in the development docker-compose.yml file
