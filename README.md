# Running it with Docker

```
docker-compose build
docker-compose up -d
```

Monitor tasks at http://localhost:5555/

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
