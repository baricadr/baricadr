#!/bin/bash

# A script to initialize a test bucket in a Minio container using a minioc container

docker-compose -f docker-compose.dev.yml exec minioc mc alias set minio http://minio:9000 admin password

docker-compose -f docker-compose.dev.yml exec minioc mc mb minio/remote-test-repo

docker-compose -f docker-compose.dev.yml exec minioc mc cp -r test-repo minio/remote-test-repo
