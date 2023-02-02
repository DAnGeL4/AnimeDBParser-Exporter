#!/bin/sh
# start Redis
log_file='redis_up.log'
# shutdown if started before
redis-cli shutdown
redis-server --bind 127.0.0.1 &
echo "Started..." >> log_file

redis-cli shutdown
echo "...stoped." >> log_file