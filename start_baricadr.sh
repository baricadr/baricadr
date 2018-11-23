#/bin/bash

flask db upgrade

atd

echo "sleep 10; curl http://localhost/zombie" | at now

/usr/bin/supervisord
