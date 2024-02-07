#--Start imports block
#System imports
import os
import json
import logging
import typing as typ
import multiprocessing as mp
from pathlib import Path
from redis.commands.json import JSON as RedisJSON
from redis.commands.json.path import Path as RedisJSONPath

#Custom imports
from configs.settings import JSON_DUMPS_DIR, REDIS_TITLES_DUMPS_STORE_KEY
from lib.types import (
    WatchListType, ServerAction, EnabledDataHandler,
    TitlesProgressStatus, TitlesProgressStatusCurrent,
    EnabledProgressHandler,
    DEFAULT_PROGRESS_HANDLER, DEFAULT_DATA_HANDLER
)
from lib.interfaces import IDataHandler, IProgressHandler
from lib.tools import OutputLogger
from modules.common.application_objects import redis
#--Finish imports block


#--Start global constants block
#--Finish global constants block


#--Start functional block
class JSONDataHandler(IDataHandler):
    '''
    Contains methods for working with the json data files.
    Simulates work with a dictionary.
    '''
    _dump_file_name: typ.Union[str, Path]

    def __init__(self, data: dict = {}, module_name: str = '', 
                 logger_suffix: str = '', queue: mp.Queue = None, **kwargs):
        arg_dump_name = 'dump_file_name'
        assert arg_dump_name in kwargs, f"Missing '{arg_dump_name}' argument."

        _ = super().__init__(dict(data))

        _logger_name = "json_handler"
        if logger_suffix:
            _logger_name += "_" + logger_suffix

        self._module_name = module_name
        self._dump_file_name = kwargs[arg_dump_name]
        self._logger = OutputLogger(duplicate=True,
                                    queue=queue,
                                    name=_logger_name
                                   ).logger

    def _load_json_data(self) -> typ.Dict[str, typ.Any]:
        '''
        Loads JSON data from a file for a specific module.
        '''
        json_data = {}
        file_path = os.path.join(JSON_DUMPS_DIR, self._dump_file_name)

        self._logger.info(f"Loading json dump for {self._module_name} module...")
        try:
            with open(file_path) as file:
                json_data = json.load(file)
        except:
            json_data = {}

        if not json_data:
            self._logger.error("...error.")
        else:
            self._logger.success("...loaded.")
        return json_data

    def _prepare_json_data(self, type_: WatchListType) -> typ.Dict[str, typ.Any]:
        '''
        Prepares data into a valid format for JSON.
        '''
        key = type_.value if hasattr(type_, 'value') else type_
        if not key in self:
            self[key] = dict()

    def _save_data_to_json(self) -> bool:
        '''
        Saves anime data in JSON format to a file 
        for a specific module.
        '''
        file_path = os.path.join(JSON_DUMPS_DIR, self._dump_file_name)
        json_object = json.dumps(self, indent=4, ensure_ascii=False)

        self._logger.info(f"Saving json dump for {self._module_name} module...")

        try:
            with open(file_path, 'w') as file:
                file.write(json_object)
        except:
            self._logger.error("...error.")
            return False

        self._logger.success("...saved.")
        return True

    def load_data(self, *args, **kwargs) -> typ.NoReturn:
        '''
        Loads data from the json file.
        '''
        json_data = self._load_json_data(*args, **kwargs)
        
        _ = self.clear()
        _ = self.update(dict(json_data))

    def prepare_data(self, *args, **kwargs) -> typ.NoReturn:
        '''
        Prepares json data.
        '''
        _ = self._prepare_json_data(*args, **kwargs)

    def save_data(self, *args, **kwargs) -> bool:
        '''
        Stores data in the destination json file.
        '''
        return self._save_data_to_json(*args, **kwargs)

        
class CacheDataHandler(IDataHandler):

    def __init__(self, data: dict = dict(), module_name: str = '',
                 queue: mp.Queue = None, **kwargs):
        _ = super().__init__(dict(data))
        self._module_name = module_name
                     
        logger_arg_name = 'logger'
        if logger_arg_name in kwargs:
            self._logger = kwargs[logger_arg_name]
        else:
            self._logger = OutputLogger(duplicate=True,
                                        queue=queue,
                                        name="cache_handler"
                                       ).logger

    def __setitem__(self, key, item):
        if type(item) is dict:
            logger = None
            
            if hasattr(self, '_logger'):
                logger=self._logger
                
            item = self.__class__(item, logger=logger)
            
        self.__dict__[key] = item

    def __getitem__(self, key):
        return self.__dict__[key]

    def __repr__(self):
        return repr(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __delitem__(self, key):
        del self.__dict__[key]

    def clear(self):
        return self.__dict__.clear()

    def copy(self):
        return self.__dict__.copy()

    def has_key(self, k):
        return k in self.__dict__

    def update(self, *args, **kwargs):
        return self.__dict__.update(*args, **kwargs)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def pop(self, *args):
        return self.__dict__.pop(*args)

    def __cmp__(self, dict_):
        return self.__cmp__(self.__dict__, dict_)

    def __contains__(self, item):
        return item in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)

    def __unicode__(self):
        return repr(self.__dict__)


class RedisJSONDataHandler(IDataHandler):
    '''
    Contains methods for working with data
    in Redis JSON format.
    Note: using handler['key.key'] faster than handler['key']['key'] 
    (1 vs 2 & more calls to redisdb).
    '''

    _module_name: str = None
    _logger: logging.Logger = None
    _top_level_key: str = None
    _current_key: RedisJSONPath = None
    _redis_store: RedisJSON = None

    def __init__(self, data: dict = {}, module_name: str = '', 
                 logger_suffix: str = '', queue: mp.Queue = None, **kwargs):
        self._module_name = module_name
        _ = self._set_logger(logger_suffix, queue, **kwargs)
        _ = self._set_redis_store(**kwargs)
        _ = self._set_top_level_key(**kwargs)
        _ = self._set_current_key(**kwargs)

        if data:
            _ = self._redis_store.set(
                self._top_level_key, self._current_key, data)

    def _set_logger(self, logger_suffix: str, 
                    queue: mp.Queue, **kwargs) -> typ.NoReturn:
        '''Sets logger for the handler.'''
        _logger = kwargs.get('logger', None)
        if not _logger:
            _logger_name = "redis_handler"
            if logger_suffix:
                _logger_name += "_" + logger_suffix

            _logger = OutputLogger(duplicate=True, queue=queue,
                                   name=_logger_name).logger

        self._logger = _logger

    def _сompose_top_level_key(self, **kwargs) -> str:
        '''
        Composes the top level key for the Redis JSON path 
        from dump file name.
        '''
        arg_dump_name = 'dump_file_name'
        assert arg_dump_name in kwargs, f"Missing '{arg_dump_name}' argument."

        dump_file_path = kwargs.get(arg_dump_name)
        file_name = dump_file_path.split('/')[-1]
        user_module = file_name.split('.')[0]
        return f"{REDIS_TITLES_DUMPS_STORE_KEY}:{user_module}"

    def _top_level_key_exists(self) -> bool:
        '''
        Checks if the top level key exists in RedisDB.
        '''
        root_path = RedisJSONPath(RedisJSONPath.root_path())
        answ = self._redis_store.get(self._top_level_key, root_path)
        res = True
        if not answ:
            res = False
        return res

    def _set_top_level_key(self, **kwargs) -> None:
        '''
        Sets the top level key as the Redis JSON path.
        '''
        self._top_level_key = kwargs.get('top_level_key', None)
        if not self._top_level_key:
            self._top_level_key = self._сompose_top_level_key(**kwargs)

        if not self._top_level_key_exists():
            root_path = RedisJSONPath(RedisJSONPath.root_path())
            self._redis_store.set(self._top_level_key, root_path, {})

    def _set_redis_store(self, **kwargs) -> None:
        '''
        Sets the redis store for working with the dumps.
        '''
        self._redis_store = kwargs.get("store", None)
        if self._redis_store is None:
            self._redis_store = redis.json()
            _ = self._set_current_key(**kwargs)

    def _set_current_key(self, **kwargs) -> None:
        '''
        Sets the current key as the Redis JSON path.
        '''
        current_key: RedisJSONPath = kwargs.get("current_key", None)
        if current_key:
            assert type(current_key) is RedisJSONPath, \
                "Invalid type of 'current_key' argument."
            self._current_key = current_key

        elif self._current_key is None:
            self._current_key = RedisJSONPath(RedisJSONPath.root_path())

    def _json_key_type_array(self, key: RedisJSONPath = None) -> bool:
        '''
        Checks if the key is an array.
        '''
        key = self._current_key if key is None else key
        json_key_type = self._redis_store.type(
                self._top_level_key, key)

        res = True if json_key_type == 'array' else False
        return res

    def _compose_redis_json_key(self, key: RedisJSONPath, 
                                check_type: bool = True) -> RedisJSONPath:
        '''
        Composes the Redis JSON path key for several types.
        '''
        if check_type and self._json_key_type_array():
            assert type(key) is int, "Type of 'key' argument must be 'int'."
            key = RedisJSONPath(f"{self._current_key.strPath}[{key}]")
        elif self._current_key.strPath == RedisJSONPath.root_path():
            key = RedisJSONPath(f"{self._current_key.strPath}{key}")
        else:
            key = RedisJSONPath(f"{self._current_key.strPath}.{key}")
        return key

    def __getitem__(self, key):
        key = self._compose_redis_json_key(key)
        value = self._redis_store.get(self._top_level_key, key)
        value = self.__class__(store=self._redis_store, 
                               top_level_key=self._top_level_key, 
                               current_key=key)
        return value

    def __setitem__(self, key, value):
        key = self._compose_redis_json_key(key)
        _ = self._redis_store.set(self._top_level_key, key, value)

    def __repr__(self):
        current_key = self._redis_store.get(
            self._top_level_key, self._current_key)
        return repr(current_key)

    def __len__(self):
        keys_count = -1
        if self._json_key_type_array():
            keys_count = self._redis_store.arrlen(
                self._top_level_key, self._current_key)
        else:
            keys_count = self._redis_store.objlen(
                self._top_level_key, self._current_key)
        return keys_count

    def __delitem__(self, key):
        key = self._compose_redis_json_key(key)
        _ = self._redis_store.delete(self._top_level_key, key)

    def clear(self):
        res = self._redis_store.clear(
            self._top_level_key, self._current_key)
        return res

    def copy(self):
        raise NotImplementedError

    def has_key(self, key):
        keys = self.keys()
        return key in keys

    def update(self, *args, **kwargs):
        if len(args) > 1:
            raise TypeError("TypeError: update expected "\
                            "at most 1 argument, got 2")

        args_dict = args[0] if args else {}
        merged_dict = {**args_dict, **kwargs}
        #JSON.MERGE not availible in RedisJSON version < 2.6.0
        #res = self._redis_store.merge(
        #    self._top_level_key, self._current_key, merged_dict)

        res = True
        for key, value in merged_dict.items():
            key = self._compose_redis_json_key(key, check_type=False)
            tmp_res = self._redis_store.set(self._top_level_key, key, value)
            res = False if not tmp_res else res
        return res

    def keys(self):
        keys = self._redis_store.objkeys(
            self._top_level_key, self._current_key)
        return keys

    def values(self):
        raise NotImplementedError

    def items(self):
        raise NotImplementedError

    def pop(self, *args):
        raise NotImplementedError

    def __cmp__(self, dict_):
        raise NotImplementedError

    def __contains__(self, key):
        return self.has_key(key)

    def __iter__(self):
        raise NotImplementedError

    def __unicode__(self):
        current_key = self._redis_store.get(
            self._top_level_key, self._current_key)
        return repr(current_key)

    def _prepare_data_for_redis(self, type_: str) -> typ.NoReturn:
        '''
        Prepares data into a valid format for Redis storage.
        '''
        key = type_.value if hasattr(type_, 'value') else type_
        if not key in self:
            self[key] = dict()

    def prepare_data(self, *args, **kwargs) -> typ.NoReturn:
        '''
        Prepares data for saving to Redis based on the arguments passed.
        '''
        _ = self.clear()
        _ = self._prepare_data_for_redis(*args, **kwargs)

    def load_data(self, *args, **kwargs) -> typ.NoReturn:
        '''
        Loads data from Redis based on the arguments passed.
        '''
        #Implementation unused
        pass

    def save_data(self, *args, **kwargs) -> typ.NoReturn:
        '''
        Saves data to Redis based on the arguments passed.
        '''
        #Implementation unused
        pass


class CacheProgressHandler(IProgressHandler):
    '''
    Contains methods for working with progress data 
    for a progress bar template.
    '''

    @property
    def progress(self) -> typ.Union[TitlesProgressStatus, None]:
        '''
        Returns progress data from the storage by action.
        '''
        if self._action is ServerAction.PARSE:
            return self._storage.cached_progress_parser
            
        elif self._action is ServerAction.EXPORT:
            return self._storage.cached_progress_exporter
            
        return None
        
    @progress.setter
    def progress(self, progress: TitlesProgressStatus) -> typ.NoReturn:
        '''
        Stores progress data in storage by action.
        '''
        if self._action is ServerAction.PARSE:
            self._storage.cached_progress_parser = progress
        elif self._action is ServerAction.EXPORT:
            self._storage.cached_progress_exporter = progress

    def initialize_progress(self, status: bool = False,
                            n_now: int = 0, n_max: int = 0) -> typ.NoReturn:
        '''
        Clears progress data from storage 
        and reinitializes new ones.
        The current progress is set by default.
        '''
        progress = TitlesProgressStatus(status=status)
        progress.all.now = n_now
        progress.all.max = n_max

        self.progress = progress

    def initialize_progress_curr(self, watch_list: WatchListType,
                                   n_now: int = 0, n_max: int = 0) -> typ.NoReturn:
        '''
        Initializes the current progress data 
        and writes to the common progress data in the storage.
        '''
        current_progress = TitlesProgressStatusCurrent(
            now=n_now, max=n_max, watchlist=watch_list.value)

        progress = self.progress
        progress.current = current_progress
        self.progress = progress

    def increase_progress_all(self) -> typ.NoReturn:
        '''
        Increases the total number of processed titles.
        '''
        progress = self.progress

        if progress:
            progress.all.now += 1
            self.progress = progress

    def increase_progress_curr(self, inc_prgs_all: bool = True) -> typ.NoReturn:
        '''
        Increases the number of processed titles 
        in the current processing. 
        Increases the total number 
        of titles processed, if specified.
        '''
        progress = self.progress
        if progress:
            progress.current.now += 1
            
            if inc_prgs_all:
                progress.all.now += 1
                
            self.progress = progress


DataHandlersCompatibility: typ.Dict[EnabledDataHandler, IDataHandler] = {
    EnabledDataHandler.JSON: JSONDataHandler,
    EnabledDataHandler.CACHE: CacheDataHandler,
    EnabledDataHandler.REDIS: RedisJSONDataHandler
}
ProgressHandlersCompatibility: \
            typ.Dict[EnabledProgressHandler, IProgressHandler] = {
    EnabledProgressHandler.CACHE: CacheProgressHandler,
}
DefaultDataHandler = DataHandlersCompatibility[DEFAULT_DATA_HANDLER]
DefaultProgressHandler = ProgressHandlersCompatibility[DEFAULT_PROGRESS_HANDLER]

#--Finish functional block