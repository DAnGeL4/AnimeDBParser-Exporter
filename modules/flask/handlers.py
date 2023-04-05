#--Start imports block
#System imports
import os
import json
import typing as typ
import multiprocessing as mp
from pathlib import Path

#Custom imports
from configs.settings import JSON_DUMPS_DIR
from lib.types import (
    WatchListType, ServerAction, EnabledDataHandler,
    TitlesProgressStatus, TitlesProgressStatusCurrent,
    EnabledProgressHandler, 
    DEFAULT_PROGRESS_HANDLER, DEFAULT_DATA_HANDLER
)
from lib.interfaces import IDataHandler, IProgressHandler
from lib.tools import OutputLogger
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

    def __init__(self, data: dict = dict(), module_name: str = '',
                 queue: mp.Queue = None, **kwargs):
        dump_arg_name = 'dump_file_name'
        assert dump_arg_name in kwargs, f"Missing '{dump_arg_name}' argument."
                     
        _ = super().__init__(dict(data))

        self._module_name = module_name
        self._dump_file_name = kwargs[dump_arg_name]
        self._logger = OutputLogger(duplicate=True,
                                    queue=queue,
                                    name="json_handler"
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

    def _prepare_json_data(self, type: WatchListType) -> typ.Dict[str, typ.Any]:
        '''
        Prepares data into a valid format for JSON.
        '''
        key = type.value if hasattr(type, 'value') else type
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

    def load_data(self, *args, **kwargs):
        '''
        Loads data from the json file.
        '''
        json_data = self._load_json_data(*args, **kwargs)
        
        _ = self.clear()
        _ = self.update(dict(json_data))

    def prepare_data(self, *args, **kwargs):
        '''
        Prepares json data.
        '''
        _ = self._prepare_json_data(*args, **kwargs)

    def save_data(self, *args, **kwargs):
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
        


class RedisDataHndler:
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
    EnabledDataHandler.REDIS: RedisDataHndler
}
ProgressHandlersCompatibility: \
            typ.Dict[EnabledProgressHandler, IProgressHandler] = {
    EnabledProgressHandler.CACHE: CacheProgressHandler,
}
DefaultDataHandler = DataHandlersCompatibility[DEFAULT_DATA_HANDLER]
DefaultProgressHandler = ProgressHandlersCompatibility[DEFAULT_PROGRESS_HANDLER]

#--Finish functional block