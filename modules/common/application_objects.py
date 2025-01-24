#--Start imports block
#System imports
from redis import Redis
from flask import Flask
from flask_session import Session
from flask_caching import Cache
from celery import Celery

#Custom imports
from configs.settings import (
    FLASK_SESSION_FILE_DIR, FLASK_CACHE_DIR, 
    FLASK_APPLICATION_NAME, FLASK_SECRET_KEY, 
    FLASK_SESSION_FILE_THRESHOLD, FLASK_SESSION_TYPE, 
    FLASK_SESSION_TIME_TO_LIVE, FLASK_CACHE_TYPE, 
    FLASK_CACHE_TIME_TO_LIVE, CELERY_RESULT_BACKEND, 
    CELERY_BROKER_URL, CELERY_USE_PICKLE_SERIALIZER, 
    REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB
)
from lib.factory import FlaskFactory, CeleryFactory
#--Finish imports block


#--Start global constants block
flask_app: Flask = FlaskFactory.make_flask_application(
    name=FLASK_APPLICATION_NAME,
    flask_secret_key=FLASK_SECRET_KEY,
    session_type=FLASK_SESSION_TYPE,
    session_dir=FLASK_SESSION_FILE_DIR,
    session_ttl=FLASK_SESSION_TIME_TO_LIVE,
    session_thresh=FLASK_SESSION_FILE_THRESHOLD,
    cache_type=FLASK_CACHE_TYPE,
    cache_dir=FLASK_CACHE_DIR,
    cache_ttl=FLASK_CACHE_TIME_TO_LIVE,
)
celery: Celery = CeleryFactory.make_celery(
    app=flask_app,
    backend=CELERY_RESULT_BACKEND,
    broker=CELERY_BROKER_URL,
    using_serializer=CELERY_USE_PICKLE_SERIALIZER
)
flask_sess: Session = FlaskFactory.make_flask_session(flask_app)
flask_cache: Cache = FlaskFactory.make_flask_cache(flask_app)
redis: Redis = Redis(host=REDIS_HOST, 
    port=REDIS_PORT, 
    password=REDIS_PASSWORD,
    db=REDIS_DB, 
    decode_responses=True
)
#--Finish global constants block