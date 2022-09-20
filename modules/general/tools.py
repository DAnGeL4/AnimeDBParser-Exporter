#--Start imports block
#System imports
import sys
import logging
import traceback
import functools
import typing as typ
import multiprocessing as mp
from types import TracebackType
from contextlib import redirect_stdout
from logging.handlers import QueueHandler
#Custom imports
from configs import settings as cfg
#--Finish imports block


#--Start decorators block
class OutputLogger:
    '''
    Logger class to configure the configuration 
    of the logger and convenient work with logs.
    '''
    _log_format = "%(asctime)s [%(levelname)s] %(message)s"
    _datefmt = '%y-%m-%d %H:%M'
    _formatter = logging.Formatter(_log_format, datefmt=_datefmt)
    
    def __init__(self, duplicate: bool, queue=None, 
                 name: str="general", level: str="INFO") -> typ.NoReturn:
        self.logger = logging.getLogger(name)
        self.name = self.logger.name
        _ = self._add_logger_success_level()
                     
        self._level = getattr(logging, level)
        self._queue = queue

        self.logger.handlers.clear()
        handlers = self._get_handlers(duplicate, queue)
        _ = self._add_handlers(handlers)
                     
        self.logger.setLevel(self._level)
        self.logger.propagate = False
                     
        self._redirector = redirect_stdout(self)

    @staticmethod
    def base_configure_logging(level=None) -> typ.NoReturn:
        '''Configures the logging system.'''
        level = logging.INFO if not level else level
        logging.basicConfig(
            level=level,
            format=OutputLogger._log_format,
            datefmt=OutputLogger._datefmt
        )

    def _add_logger_success_level(self) -> typ.NoReturn:
        '''
        Adds a new logging level for success type.
        '''
        logging.SUCCESS = 25  # between WARNING and INFO
        logging.addLevelName(logging.SUCCESS, 'SUCCESS')
        setattr(self.logger, 'success', lambda message, 
                *args: self.logger._log(logging.SUCCESS, message, args))

    @classmethod
    def _get_handlers(cls, duplicate: bool, queue) -> typ.List[logging.Handler]:
        '''Checks and returns a list of handlers for logging.'''
        handlers = list([])
        if queue:
            handler = QueueHandler(queue)
            handlers.append(
                handler
            )
            return handlers
        
        if cfg.WRITE_LOG_TO_FILE:
            handler = logging.FileHandler(cfg.GLOBAL_LOG_FILE)
            handler.setFormatter(cls._formatter)
            handlers.append(
                handler
            )
            
        if duplicate or not cfg.WRITE_LOG_TO_FILE:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(cls._formatter)
            handlers.append(
                handler
            )
            
        return handlers

    def _add_handlers(self, handlers: typ.List[logging.Handler]) -> typ.NoReturn:
        '''Adds handlers for the logger, if not yet added.'''
        if len(self.logger.handlers) > 0: return
        for handler in handlers:
            self.logger.addHandler(handler)

    def write(self, msg: str) -> typ.NoReturn:
        '''Writes to the log.'''
        if msg and not msg.isspace():
            self.logger.log(self.level, msg)

    def flush(self) -> typ.NoReturn: pass

    def __enter__(self) -> 'OutputLogger':
        self._redirector.__enter__()
        return self

    def __exit__(self, exc_type: typ.Union[typ.Type[BaseException], None], 
                 exc_value: typ.Union[BaseException, None],
                 traceback: typ.Union[TracebackType, None]) -> typ.NoReturn:
        self._redirector.__exit__(exc_type, exc_value, traceback)

    @staticmethod
    def redirect_output(redirected_function: typ.Callable,
                       duplicate: bool=True) -> typ.Callable:
        '''
        Redirects output to #OutputLogger instance 
        for #redirected_function. After returns stdout back.
        '''
        @functools.wraps(redirected_function)
        def wrapper(*args, **kwargs):
            
            if cfg.WRITE_LOG_TO_FILE:
                with OutputLogger(duplicate):
                    res = redirected_function(*args, **kwargs)
            else:
                res = redirected_function(*args, **kwargs)
    
            return res
    
        return wrapper


class ListenerLogger:
    '''
    The class of a listener for working with 
    a log through a queue.
    '''
    def __init__(self, queue: mp.Queue):
        self._records_container = dict()
        self._queue = queue
        
        redir_out = OutputLogger(duplicate=True, name="listener")
        self._logger = redir_out.logger

    def listener_process(self) -> typ.NoReturn:
        '''Starts to listen, sorts and process records in queue.'''
        while True:
            try:
                record = self._queue.get()
                if record is None: break
                    
                rec_key = f"{record.processName}_{record.threadName}"
                if record.name is None:
                    records_by_key = self._records_container.pop(rec_key)
                    for record in records_by_key:
                        self._logger.handle(record)
                    continue

                if rec_key not in self._records_container:
                    self._records_container[rec_key] = list()
                self._records_container[rec_key].append(record)
                
            except Exception:
                print('Something wrong:', file=sys.stderr)
                traceback.print_exc(file=sys.stderr)

    def get_listener_proc(self) -> mp.Process:
        '''Returns the prepared process of the listener.'''
        return mp.Process(target=self.listener_process)

    def stop_listener_queue(self) -> typ.NoReturn:
        '''Sends the end of queue for the listener.'''
        self._queue.put_nowait(None)

    @staticmethod
    def send_stop_msg(redirected_function: typ.Callable) -> typ.Callable:
        '''Sends a stop message of current process for listener..'''
        @functools.wraps(redirected_function)
        def wrapper(self, *args, **kw):   
            res = redirected_function(self, *args, **kw)
            if self._queue:
                rec = self._logger.makeRecord(None, *([0] * 6))
                self._logger.handle(rec)
            return res
            
        return wrapper
        
    @staticmethod
    def listener_preparing(redirected_function: typ.Callable) -> typ.Callable:
        '''
        Preparation of the listener's process 
        for sorting Log messages from redirected function.
        '''
        @functools.wraps(redirected_function)
        def wrapper(self, *args, **kw):      
            self._queue = mp.Manager().Queue(-1)
            self.set_new_logger(True, name="multi_proc_run")
                                              
            listener_logger = ListenerLogger(self._queue)
            listener = listener_logger.get_listener_proc()
            listener.start()
            
            res = redirected_function(self, *args, **kw)
                
            listener_logger.stop_listener_queue()
            listener.join()
                    
            self.set_default_logger()
            return res
            
        return wrapper

#--Finish decorators block