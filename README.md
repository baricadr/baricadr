# Running it with Docker

```
docker-compose build
docker-compose up -d
```

Monitor tasks at http://localhost:5555/
See emails at http://localhost:8025/

# Running it manually

## To install dependencies

`make setup`

## To launch the web part

`make run`
(or `make dev` to run in development mode = auto reload modified python code)

## Then the Redis queue

`docker run --name some-redis -d -p 6379:6379 redis`

## And Celery

`make celery`

# Testing it

## Triggering a "pull"

`curl  -H "Content-type: application/json" -X POST http://localhost:5000/pull -d '{"files": "/groups/bipaa/archive/prout.gz"}'`

## Checking the status

`curl  -H "Content-type: application/json" -X GET http://localhost:5000/status/<pull-id>`

With pull-id = the return of the pull POST call above

# Configuring

There are 3 run mode for baricadr: `dev`, `test` and `prod`.

To enable development mode you should set the `BARICADR_RUN_MODE` environment variable to `dev`. It is set by default in the development docker-compose.yml file. Among other things it will display more logs.

This variable can be set to `test` or `prod` values. The default is `prod`.

To override the configuration of the selected run mode, you need to create a file `local.cfg`, by copying `local.example.cfg`. Every config written in this file will override the default one.

You should write a yaml file containing the list of repositories managed by Baricadr. Use this syntax:

```
/groups/bipaa/archive:
    backend: sftp # Pourrait être ssh, ftp, http, s3, ... (rclone ?)
    url: adr-xxx-xxx.inra.fr
    user: gogepp
    password: xxxxx
    exclude: *xml

/groups/brassica/db:
    backend: s3 # Pourrait être ssh, ftp, http, s3, ... (rclone ?)
    url: google
    user: gogepp
    password: xxxxx
    exclude: *xml
```

You must set the `BARICADR_REPOS_CONF` environment variable to the path to this yaml file, or define it in the `local.cfg` config file. A test one is used by default in the development docker-compose.yml file
