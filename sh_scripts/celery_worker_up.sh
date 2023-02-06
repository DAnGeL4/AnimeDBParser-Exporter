#!/bin/bash
celery_log_file=$1
celery_tasks=modules.flask.application.celery
echo "" >> $celery_log_file
echo "** RUN celery_worker_up.sh..." | tee -a $celery_log_file
answer='**.FINISH celery_worker_up.sh. DONE'

is_running=$(celery -A $celery_tasks status 2>/dev/null  &)
wait $!

# Checking if Celery is running
if [[ "$is_running" = *"OK"* ]]
then
    echo "...CELERY IS ALREDY RUNNING..." | tee -a $celery_log_file
else
    # Starting Celery
    (celery -A $celery_tasks worker -P processes --loglevel=info --logfile=$celery_log_file &)
    
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
        answer="**..CELERY NOT STARTED. FAIL"
    fi

fi
echo "$answer"  | tee -a $celery_log_file