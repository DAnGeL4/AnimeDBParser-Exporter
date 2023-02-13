#--Start imports block
#System imports
import os
import functools
import typing as typ

#Custom imports
from configs.settings import ServerAction
from configs.connected_modules import ModuleAnimeBuffRu, ModuleAnimeGoOrg
from modules.general.tools import OutputLogger
from modules.general.main_tools import MainService

import modules.flask.application as flask_app
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

    #user select
    #temporary solution
    selected_modules = dict({
        ServerAction.PARSE: ModuleAnimeBuffRu(
            cookies=os.environ['animebuff_session_value']
        ),
        ServerAction.EXPORT: ModuleAnimeGoOrg(
            cookies=os.environ['animego_REMEMBERME']
        )
    })
    selected_action = ServerAction.EXPORT
    #----
    
    #_ = m_serv.processing_for_selected_module(selected_action, selected_modules)

    flask_app.run_app()
    
    return
        
#--Finish main block

    
#--Start run block
OutputLogger.base_configure_logging()
_ = main()
#--Finish run block