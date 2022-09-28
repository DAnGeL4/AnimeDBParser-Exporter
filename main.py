#--Start imports block
#System imports
import functools
import typing as typ
#Custom imports
from configs import abstract_classes as ac
from configs.settings import WatchListTypes
from configs.settings import ENABLE_PARSING_MODULE, ENABLE_EXPORTER_MODULE
from configs.connected_modules import EnabledParserModules
from modules.general.tools import OutputLogger
from modules.general.proxy_checker import ProxyChecker
from modules.general.web_page_tools import WebPageService, WebPageParser
#--Finish imports block


#--Start decorators block
def basic_output(redirected_function: typ.Callable) -> typ.Callable:
    '''Prints basic messages for the main function.'''
    
    @functools.wraps(redirected_function)
    def wrapper(*args, **kwargs):
        redir_out = OutputLogger(duplicate=True, name="main")
        logger = redir_out.logger
        
        logger.info("STARTED...\n")
        logger.info("-----")
        
        res = redirected_function(*args, **kwargs)
        
        logger.info("-----\n")
        logger.info("...FINISHED.\n\n")
        return res

    return wrapper
#--Finish decorators block


#--Start functional block
def parse_selected_module(module: ac.ConnectedParserModuleType) -> typ.NoReturn:
    ''''''    
    prx_chk = ProxyChecker()
    prx_chk.prepare_proxy_lists(module.config_module.url_general)

    web_serv = WebPageService(module.config_module)
    if not web_serv.get_preparing(): return
    
    for type in WatchListTypes:
        page_parser = WebPageParser(module, type)
        page_parser.parse_typed_watchlist()

def parse_all_modules(module: ac.ConnectedParserModuleType=None) -> typ.NoReturn:
    ''''''
    if module:
        parse_selected_module(module)
    else:
        for module in EnabledParserModules:
            parse_selected_module(module)
    return
#--Finish functional block


#--Start main block
@basic_output
def main() -> typ.NoReturn:
    '''Entry point.'''

    if ENABLE_PARSING_MODULE:
        _ = parse_all_modules()
    if ENABLE_EXPORTER_MODULE:
        pass
    
    return
        
#--Finish main block

    
#--Start run block
OutputLogger.base_configure_logging()
main()
#--Finish run block