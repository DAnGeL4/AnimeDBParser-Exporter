#--Start imports block
#System imports
import functools
import typing as typ

#Custom imports
from configs.connected_modules import EnabledModules
from configs.connected_modules import ModuleAnimeBuffRu, ModuleAnimeGoOrg
from modules.general.tools import OutputLogger
from modules.general.main import MainService
#--Finish imports block


#--Start decorators block
def basic_output(redirected_function: typ.Callable) -> typ.Callable:
    '''Prints basic messages for the main function.'''
    
    @functools.wraps(redirected_function)
    def wrapper(*args, **kwargs):
        redir_out = OutputLogger(duplicate=True, name="main")
        logger = redir_out.logger
        
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

    #user select
    #temporary solution
    selected_modules = dict({
        EnabledModules.parse.name: ModuleAnimeBuffRu,
        EnabledModules.export.name: ModuleAnimeGoOrg
    })
    selected_action = EnabledModules.export
    #----

    m_serv = MainService()
    _ = m_serv.processing_for_selected_module(selected_modules, 
                                              selected_action)
    
    return
        
#--Finish main block

    
#--Start run block
OutputLogger.base_configure_logging()
main()
#--Finish run block