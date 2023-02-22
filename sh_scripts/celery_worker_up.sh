#!/bin/bash
celery_log_file=$1
restart_celery=$2
celery_tasks=$3

echo "" >> $celery_log_file
echo "** RUN celery_worker_up.sh..." | tee -a $celery_log_file
answer='**.FINISH celery_worker_up.sh. DONE'

is_running=$(celery -A $celery_tasks status 2>/dev/null  &)
wait $!

# Checking if Celery is running
if [[ "$is_running" = *"OK"* ]]
then
    echo "...CELERY IS ALREDY RUNNING..." | tee -a $celery_log_file
    if $restart_celery
    then
        echo "...CELERY WILL BE RESTARTED..." | tee -a $celery_log_file
        echo "...STOPPING..." | tee -a $celery_log_file
        ps auxww | grep 'celery worker' | awk '{print $2}' | xargs kill -9 2>/dev/null
        wait $!
    fi
fi
if [[ "$is_running" != *"OK"* ]] || $restart_celery
then
    # Starting Celery
    echo "...STARTING CELERY..." | tee -a $celery_log_file
    (celery -A $celery_tasks worker -P processes --loglevel=info >> $celery_log_file 2>>$celery_log_file &)
    
    # Waiting for service start
    for (( i=0; i<5; ++i )); do
        if [[ "$(celery -A $celery_tasks status 2>/dev/null)" = *"OK"* ]]; then break; fi
        sleep 1;
    done
    
    # Checking if Celery is running
    is_running=$(celery -A $celery_tasks status 2>/dev/null  &)
    if [[ "$is_running" = *"OK"* ]]
    then
        echo "...CELERY STARTED..." | tee -a $celery_log_file
    else
        echo "...CELERY NOT STARTED..."
        answer='**.FINISH celery_worker_up.sh. FAIL'
    fi
fi

echo "$answer"  | tee -a $celery_log_file