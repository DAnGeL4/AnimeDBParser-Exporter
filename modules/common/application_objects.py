#--Start imports block
#System imports
from flask import Flask
from flask_session import Session
from flask_caching import Cache
from celery import Celery

#Custom imports
from configs.settings import (
    FLASK_SESSION_FILE_DIR, FLASK_CACHE_DIR, 
    CELERY_RESULT_BACKEND, CELERY_BROKER_URL, 
    FLASK_APPLICATION_NAME, FLASK_SESSION_FILE_THRESHOLD
)
from lib.factory import FlaskFactory, CeleryFactory
#--Finish imports block


#--Start global constants block
flask_app: Flask = FlaskFactory.make_flask_application(
    name=FLASK_APPLICATION_NAME,
    session_dir=FLASK_SESSION_FILE_DIR,
    cache_dir=FLASK_CACHE_DIR,
    session_thresh=FLASK_SESSION_FILE_THRESHOLD
)
celery: Celery = CeleryFactory.make_celery(
    app=flask_app,
    backend=CELERY_RESULT_BACKEND,
    broker=CELERY_BROKER_URL
)
flask_sess: Session = FlaskFactory.make_flask_session(flask_app)
flask_cache: Cache = FlaskFactory.make_flask_cache(flask_app)
#--Finish global constants block