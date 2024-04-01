#--Start imports block
#System imports
import functools
import typing as typ

#Custom imports
from lib.tools import OutputLogger
from modules.common.main_service import MainService
import modules.flask.application as _flask
#--Finish imports block


#--Start decorators block
def basic_output(redirected_function: typ.Callable) -> typ.Callable:
    '''Prints basic messages for the main function.'''
    
    @functools.wraps(redirected_function)
    def wrapper(*args, **kwargs):
        m_serv = MainService()
        logger = m_serv.logger
        
        logger.info("STARTED...\n")
        logger.info("-----\n")
        
        res = redirected_function(*args, **kwargs)
        
        logger.info("-----\n")
        logger.info("...FINISHED.\n\n")
        return res

    return wrapper
#--Finish decorators block


#--Start main block
@basic_output
def main() -> typ.NoReturn:
    '''Entry point.'''
    m_serv = MainService()
    if not m_serv.prepare_redis_server(): 
        m_serv.logger.error('The Redis server is not running.')
        return
        
    if not m_serv.prepare_celery_worker():
        m_serv.logger.error('The Celery worker is not running.')
        return

    _ = m_serv.initial_proxy_check()
    _ = m_serv.prepare_modules_proxies()
    _ = _flask.run_app()
    
    return
        
#--Finish main block

    
#--Start run block
OutputLogger.base_configure_logging()
_ = main()
#--Finish run block