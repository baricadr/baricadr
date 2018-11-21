#/bin/bash

flask db upgrade
/usr/bin/supervisord
