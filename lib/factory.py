#--Start imports block
#System imports
import os
import typing as typ
import dataclasses as dcls
from pathlib import Path
from flask import Flask
from flask_session import Session
from flask_caching import Cache
from celery import Celery
from collections.abc import Iterable
from pydantic import AnyHttpUrl

#Custom imports
#--Finish imports block

#--Start global constants block
#--Finish global constants block


#--Start functional block
class DataclassTypeFactory:
    '''
    Helps to simply create a data class 
    based on another class or parameter set.
    '''

    def _build_namespace_asdict(self) -> typ.Dict[str, typ.Callable]:
        '''
        Creates an asdict function for the namespace.
        '''
        namespace = {
            'asdict':
            lambda self: {k: v
                          for k, v in dcls.asdict(self).items()}
        }
        return namespace

    def _build_fields(self, fields_types: typ.List[typ.Any],
                      fields_container: typ.Iterable) -> typ.List[dcls.Field]:
        '''
        Builds the fields of the date class.
        '''
        fields = list()

        for f_type, field in zip(fields_types, list(fields_container)):
            value = field.value if hasattr(field, 'value') else field
            fields.append((value, f_type, dcls.field(default_factory=dict)))

        return fields

    def _build_dataclass_type(
            self, name: str, fields: typ.List[dcls.Field],
            namespace: typ.Dict[str, typ.Callable]) -> typ.Type:
        '''
        An internal method for build a data class.
        '''
        dataclass_type = dcls.make_dataclass(name, fields, namespace=namespace)
        return dataclass_type

    def _get_namespace(
            self,
            functions: typ.List[typ.Callable]) -> typ.Dict[str, typ.Callable]:
        '''
        Checks for existing and allowed passed functions.
        Returns a builded functions.
        '''
        namespace = dict()

        for key in functions:
            assert key in self.__enabled_namespace_builders, \
                    f'Function "{key}" not enabled or not exist.'

            namespace.update(self.__enabled_namespace_builders[key](self))

        return namespace

    def build_dataclass_type(self, name: str, fields_types: typ.List[typ.Any],
                             fields_container: typ.Iterable,
                             functions: typ.List[typ.Callable]) -> typ.Type:
        '''
        Creates a data class based on the passed parameters.
        '''
        assert isinstance(fields_container, Iterable), \
                f"Fields container {type(fields_container)} not iterable."
        assert len(fields_types) == len(list(fields_container)), \
                "The number of field types and the number of " + \
                                 "fields in the container must be equal."

        fields = self._build_fields(fields_types, fields_container)
        namespace = self._get_namespace(functions)

        dataclass_type = self._build_dataclass_type(name, fields, namespace)
        return dataclass_type

    __enabled_namespace_builders: typ.Dict[str, typ.Callable] = dict(
        {'asdict': _build_namespace_asdict})


class FlaskFactory:
    '''
    The class is used for the centralized creation 
    of the Flask application and its auxiliary extensions.
    '''

    @classmethod
    def make_flask_application(cls, 
                                name: str, 
                                flask_secret_key: str,
                                session_type: str, 
                                session_dir: Path, 
                                session_ttl: int,
                                session_thresh: int, 
                                cache_type: str, 
                                cache_dir: Path, 
                                cache_ttl: int) -> Flask:
        '''
        Initializes the Flask application.
        '''
        application = Flask(name)
        application.config.update(SECRET_KEY=flask_secret_key,
                                  SESSION_TYPE=session_type,
                                  SESSION_FILE_DIR=session_dir,
                                  SESSION_PERMANENT=True,
                                  PERMANENT_SESSION_LIFETIME=session_ttl,
                                  SESSION_FILE_THRESHOLD=session_thresh,
                                  CACHE_TYPE=cache_type,
                                  CACHE_DIR=cache_dir,
                                  CACHE_DEFAULT_TIMEOUT=cache_ttl,
                                  CELERY_TASK_TRACK_STARTED=True)
        return application

    @classmethod
    def make_flask_session(cls, application: Flask) -> Session:
        '''
        Initializes the Flask session for the Flask application.
        '''
        session_ = Session(application)
        return session_

    @classmethod
    def make_flask_cache(cls, application: Flask) -> Cache:
        '''
        Initializes the Flask cache for the Flask application.
        '''
        cache = Cache(application)
        return cache


class CeleryFactory:
    '''
    The class is used for the centralized creation 
    of the Celery application.
    '''

    @classmethod
    def make_celery(cls, app: Flask, backend: AnyHttpUrl,
                    broker: AnyHttpUrl, using_serializer: bool) -> Celery:
        '''
        Initializes the Celery application 
        by the Flask application with using 
        the Flask application context.
        '''
        celery = Celery(app.import_name, backend=backend, broker=broker)
        celery.conf.update(app.config)
                        
        if using_serializer:
            celery.conf.event_serializer = 'pickle'
            celery.conf.task_serializer = 'pickle'
            celery.conf.result_serializer = 'pickle'
            celery.conf.accept_content = ['application/json', 'application/x-python-serialize']

        class ContextTask(celery.Task):

            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask
        return celery
