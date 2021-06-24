#!/bin/bash

# A script to initialize a test bucket in a Minio container using a minioc container

docker-compose exec minioc mc alias set minio http://minio:9000 admin password

docker-compose exec minioc mc mb minio/remote-test-repo

docker-compose exec minioc mc cp -r test-repo minio/remote-test-repo
