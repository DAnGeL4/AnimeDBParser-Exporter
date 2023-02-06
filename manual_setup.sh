#!/bin/bash

# configuring Redis
#---
# donloading config file
curl -O https://raw.githubusercontent.com/redis/redis/6.2/redis.conf
wait $!
mv redis.conf "$(pwd)/configs"

# starting Redis
(redis-server "$(pwd)/configs/redis.conf" --bind 127.0.0.1 &)
for (( i=0; i<5; ++i )); do
    if [ "$(redis-cli ping 2>/dev/null)" = "PONG" ]; then break; fi
    sleep 1;
done

# changing configuration
redis-cli CONFIG SET dir "$(pwd)/var/db_dumps"
redis-cli CONFIG SET "dbfilename" "redis_dump.rdb"
redis-cli CONFIG REWRITE
redis-cli SHUTDOWN SAVE

# making an executable Redis startup script
chmod u+x "$(pwd)/sh_scripts/redis_up.sh"
#---


# configuring Celery
#---
# making an executable Celery startup script
chmod u+x "$(pwd)/sh_scripts/celery_worker_up.sh"
#---