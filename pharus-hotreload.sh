#!/bin/sh
pharus_update() {
	[ -z "$GUNICORN_PID" ] || kill $GUNICORN_PID
	gunicorn --bind 0.0.0.0:${PHARUS_PORT} pharus.server:app &
	GUNICORN_PID=$!
}
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -f -i /tmp/keys/buaws-chen.pem ec2-user@3.128.2.214 -L 3306:buaws-chen-cf-rds.c0pqrqs42ez1.us-east-2.rds.amazonaws.com:3306 -N
pharus_update
echo "[$(date -u '+%Y-%m-%d %H:%M:%S')][DataJoint]: Monitoring Pharus updates..."
INIT_TIME=$(date +%s)
LAST_MOD_TIME=$(date -r $API_SPEC_PATH +%s)
DELTA=$(expr $LAST_MOD_TIME - $INIT_TIME)
while true; do
	CURR_LAST_MOD_TIME=$(date -r $API_SPEC_PATH +%s)
	CURR_DELTA=$(expr $CURR_LAST_MOD_TIME - $INIT_TIME)
	if [ "$DELTA" -lt "$CURR_DELTA" ]; then
		echo "[$(date -u '+%Y-%m-%d %H:%M:%S')][DataJoint]: Reloading Pharus since \`$API_SPEC_PATH\` changed."
		pharus_update
		DELTA=$CURR_DELTA
	else
		sleep 5
	fi
done