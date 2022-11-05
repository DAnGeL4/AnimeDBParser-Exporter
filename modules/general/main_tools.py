#--Start imports block
#System imports
import typing as typ

#Custom imports
from configs.settings import WatchListTypes, AnimeByWatchList
from configs.settings import ENABLE_PARSING_MODULES, ENABLE_EXPORTER_MODULES
from configs.abstract_classes import ConnectedModuleType
from configs.connected_modules import EnabledModules
from modules.general.tools import OutputLogger
from modules.general.proxy_checker import ProxyChecker
from modules.general.web_page_tools import WebPageService, WebPageParser
from modules.general.web_exporter import TitleExporter
#--Finish imports block


#--Start functional block
class MainService:
    '''
    Contains the initial functionality 
    for working with modules.
    '''

    def __init__(self):
        self.logger = OutputLogger(duplicate=True, 
                                   name="main_serv").logger

    def checking_module(self, module: ConnectedModuleType, 
                        action: typ.Union[str, EnabledModules]) -> bool:
        '''
        Checks whether the module is allowed 
        and whether the action is enabled.
        '''
        allow_values = dict({
            EnabledModules.parse.name: ENABLE_PARSING_MODULES,
            EnabledModules.export.name: ENABLE_EXPORTER_MODULES,
        })
        
        if not allow_values[action]:
            self.logger.error(f"{action.capitalize()} action disabled.\n")
            return False
            
        if module not in EnabledModules[action].value:
            self.logger.error(f"{action.capitalize()} action for module " + 
                              f"{module.module_name} are disabled.\n")
            return False
            
        return True
    
    def prepare_module(self, module: ConnectedModuleType) -> bool:
        '''Performs the initial preparing for the module.'''
        prx_chk = ProxyChecker(module.module_name)
        web_serv = WebPageService(module.module_name, module.config_module)
        
        prx_chk.prepare_proxy_lists(module.config_module.url_general)
        if not web_serv.get_preparing(): return False
        return True
        
    def parse_for_selected_module(self, selected_modules: 
                                  typ.Dict[EnabledModules, ConnectedModuleType]
                                 ) -> typ.NoReturn:
        '''Launches parsing for the selected module.'''
        action = EnabledModules.parse.name
        module = selected_modules[action]
                                     
        self.logger.info("* Start parsing action " +
                          f"for module {module.module_name}...\n")

        if not self.checking_module(module, action): return
        if not self.prepare_module(module): return
            
        for type in WatchListTypes:
            page_parser = WebPageParser(module, type)
            page_parser.parse_typed_watchlist()
            
        self.logger.info("* ...parsing action " + 
                          f"for module {module.module_name} finish.\n")

    def get_dump(self, selected_modules: 
                 typ.Dict[EnabledModules, ConnectedModuleType]
                ) -> typ.Union[None, AnimeByWatchList]:
        '''
        Prepares the query module and tries to get the dump titles. 
        If the dump is None, the query module is parse.
        '''
        main_module = selected_modules[EnabledModules.export.name]
        query_module = selected_modules[EnabledModules.parse.name]
                     
        if not self.prepare_module(query_module): return None
            
        te = TitleExporter(main_module)
        titles_dump = te.get_titles_dump(query_module)
                     
        if not titles_dump: 
            self.logger.warning("Dump not exist. Trying reparse module " + 
                                f"({main_module.module_name})...")
            
            _ = self.parse_for_selected_module(selected_modules)
            titles_dump = te.get_titles_dump(query_module)
            
            if not titles_dump: 
                self.logger.critical("Dump not exist.")
                return None
                
        return titles_dump
    
    def export_for_selected_module(self, selected_modules: 
                                   typ.Dict[EnabledModules, ConnectedModuleType]
                                  ) -> typ.NoReturn:
        '''Launches export for the selected module.'''
        action = EnabledModules.export.name
        main_module = selected_modules[action]
                                      
        self.logger.info("* Start export action " + 
                          f"for module {main_module.module_name}...\n")
                                      
        if not self.checking_module(main_module, action): return
        if not self.prepare_module(main_module): return
                                      
        titles_dump = self.get_dump(selected_modules)
        if titles_dump: 
            te = TitleExporter(main_module)
            _ = te.export_titles_dump(titles_dump)
        
        self.logger.info("* ...export action " + 
                          f"for module {main_module.module_name} finish.\n")

    def processing_for_selected_module(self, 
                        selected_modules:  typ.Dict[EnabledModules, ConnectedModuleType], 
                        action: EnabledModules) -> typ.NoReturn:
        '''Performs the specified action for the selected module.'''
        act_for_mod  = dict({
            EnabledModules.parse: self.parse_for_selected_module,
            EnabledModules.export: self.export_for_selected_module
        })
                            
        self.logger.info(f"** BEGIN PROCESSING BLOCK ({action.name.upper()}) **")
        _ = act_for_mod[action](selected_modules)
        self.logger.info(f"** END PROCESSING BLOCK ({action.name.upper()}) **\n")
        
#--Finish functional block