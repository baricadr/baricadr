#!/bin/bash

###  connect to database
echo "=> Trying to connect to the database"

DB_HOST=db
: ${DB_PORT:='5432'}
: ${DB_NAME:='postgres'}
: ${DB_USER:='postgres'}
: ${DB_PASS:='postgres'}

for ((i=0;i<20;i++))
do
    DB_CONNECTABLE=$(PGPASSWORD=$DB_PASS psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -l >/dev/null 2>&1; echo "$?")
	if [[ $DB_CONNECTABLE -eq 0 ]]; then
		break
	fi
    sleep 3
done

if ! [[ $DB_CONNECTABLE -eq 0 ]]; then
	echo "Cannot connect to database"
    exit "${DB_CONNECTABLE}"
fi

# Make sure log dirs exist
mkdir -p "$LOG_FOLDER"
chown -R nginx:nginx "$LOG_FOLDER"
mkdir -p "$TASK_LOG_DIR"

# Make sure the db schema is up-to-date
flask db upgrade

# Schedule a zombie killer in a few seconds
atd
echo "sleep 10; curl http://localhost/zombie" | at now

/usr/bin/supervisord
