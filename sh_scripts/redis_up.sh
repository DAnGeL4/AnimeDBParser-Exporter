#!/bin/bash
redis_log_file=$1
echo "" >> $redis_log_file
echo "** RUN redis_up.sh..." | tee -a $redis_log_file
answer='**.FINISH redis_up.sh. DONE'

is_running=$(redis-cli ping 2>/dev/null  &)
wait $!

# Checking if Redis is running
if [ "$is_running" = "PONG" ]
then
    echo "...REDIS IS ALREDY RUNNING..." | tee -a $redis_log_file
else
    # Starting Redis
    echo "...RUN REDIS..." | tee -a $redis_log_file
    (redis-server ./configs/redis.conf --daemonize yes --bind 127.0.0.1 >> $redis_log_file 2>>$redis_log_file &)
    
    # Waiting for service start
    for (( i=0; i<5; ++i )); do
        if [ "$(redis-cli ping 2>/dev/null)" = "PONG" ]; then break; fi
        sleep 1;
    done
    
    # Checking if Redis is running
    is_running=$(redis-cli ping 2>/dev/null  &)
    if [ "$is_running" = "PONG" ]
    then
        echo "...REDIS STARTED..." | tee -a $redis_log_file
    else
        answer="**..REDIS NOT STARTED. FAIL"
    fi

fi
echo "$answer"  | tee -a $redis_log_file