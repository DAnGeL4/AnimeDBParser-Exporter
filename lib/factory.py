#--Start imports block
#System imports
import typing as typ
import dataclasses as dcls
from flask import Flask
from celery import Celery
from collections import Iterable

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


class CeleryFactory:

    @classmethod
    def make_celery(cls, app: Flask) -> Celery:
        celery = Celery(
            app.import_name,
            backend=app.config['CELERY_RESULT_BACKEND'],
            broker=app.config['CELERY_BROKER_URL']
        )
        celery.conf.update(app.config)
    
        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
    
        celery.Task = ContextTask
        return celery