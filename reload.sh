#!/bin/sh
PRIMARY_PID="$1"
# kill background process if previously set
[ -z "$PRIMARY_PID" ] || kill "$PRIMARY_PID"
# determine reload mode
if [ "$PHARUS_MODE" == "DEV" ]; then
    export DEBUG=1
    export FLASK_ENV=development
    pharus &
else
    gunicorn --bind "0.0.0.0:${PHARUS_PORT}" pharus.server:app &
fi
PRIMARY_PID="$!"
echo "$PRIMARY_PID"
