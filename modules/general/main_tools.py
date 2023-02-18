#--Start imports block
#System imports
import subprocess
import typing as typ
from pathlib import Path

#Custom imports
from configs.settings import (
    WatchListType, AnimeByWatchList, 
    ServerAction, ENABLE_PARSING_MODULES, 
    ENABLE_EXPORTER_MODULES, COMMON_BASH_LOG_FILE, 
    REDIS_SETUP_SH_FILE, CELERY_SETUP_SH_FILE
)
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

    def is_allowed_action(self, action: ServerAction) -> bool:
        '''
        Checks whether the action is enabled.
        '''
        allow_values = dict({
            ServerAction.PARSE: ENABLE_PARSING_MODULES,
            ServerAction.EXPORT: ENABLE_EXPORTER_MODULES,
        })
        return allow_values[action]
        

    def checking_module(self, module: ConnectedModuleType, 
                        action: ServerAction) -> bool:
        '''
        Checks whether the module is allowed 
        and whether the action is enabled.
        '''
        if not self.is_allowed_action(action):
            self.logger.error(f"{action.name} action disabled.\n")
            return False
            
        if type(module) not in EnabledModules[action.value].value:
            self.logger.error(f"{action.name} action for module " + 
                              f"{module.module_name} are disabled.\n")
            return False
            
        return True

    def prepare_modules_proxies(self) -> typ.NoReturn:
        '''
        Performs an initial proxy check 
        for enabled modules for allowed actions.
        '''
        for modules_by_action in EnabledModules:
            action = ServerAction(modules_by_action.name)
                
            self.logger.info(f"Started preparing for {action.name} modules.")
            
            if not self.is_allowed_action(action):
                self.logger.warning(f"{action.name} action disabled.\n")
                continue
            
            for module in modules_by_action.value:
                self.logger.info("...preparing for module - " \
                                 f"{module.module_name}.")
                
                prx_chk = ProxyChecker(module.module_name)
                _ = prx_chk.prepare_proxy_lists(
                            module.config_module.url_general)
                
                self.logger.info("Preparing for module - " \
                                 f"{module.module_name} is done.")
                
            self.logger.info(f"Finished preparing for {action.name} modules.\n")
    
    def prepare_module(self, module: ConnectedModuleType, **kwargs) -> bool:
        '''Performs the initial preparing for the module.'''
        web_serv = WebPageService(module.module_name, module.config_module)
        if not web_serv.get_preparing(**kwargs): return False
        return True
        
    def parse_for_selected_module(self, selected_modules: 
                                  typ.Dict[ServerAction, ConnectedModuleType]
                                 ) -> typ.NoReturn:
        '''Launches parsing for the selected module.'''
        action = ServerAction.PARSE
        module = selected_modules[action]
                                     
        self.logger.info("* Start parsing action " +
                          f"for module {module.module_name}...\n")

        if not self.checking_module(module, action): return
        if not self.prepare_module(module): return
            
        for type in WatchListType:
            page_parser = WebPageParser(module, type)
            page_parser.parse_typed_watchlist()
            
        self.logger.info("* ...parsing action " + 
                          f"for module {module.module_name} finish.\n")

    def get_dump(self, selected_modules: 
                 typ.Dict[ServerAction, ConnectedModuleType]
                ) -> typ.Union[None, AnimeByWatchList]:
        '''
        Prepares the query module and tries to get the dump titles. 
        If the dump is None, the query module is parse.
        '''
        main_module = selected_modules[ServerAction.EXPORT]
        query_module = selected_modules[ServerAction.PARSE]
                     
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
                                   typ.Dict[ServerAction, ConnectedModuleType]
                                  ) -> typ.NoReturn:
        '''Launches export for the selected module.'''
        action = ServerAction.EXPORT
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

    def processing_for_selected_module(self, action: ServerAction, 
                                       selected_modules:  typ.Dict[ServerAction, ConnectedModuleType]
                                      ) -> typ.NoReturn:
        '''Performs the specified action for the selected module.'''
        act_for_mod  = dict({
            ServerAction.PARSE: self.parse_for_selected_module,
            ServerAction.EXPORT: self.export_for_selected_module
        })
                            
        self.logger.info(f"** BEGIN PROCESSING BLOCK ({action.name}) **")
        _ = act_for_mod[action](selected_modules)
        self.logger.info(f"** END PROCESSING BLOCK ({action.name}) **\n")

    def run_setup_script(self, setup_file: Path, args: typ.List[typ.Any]) -> bool:
        '''
        Runs the specified bash script 
        with the specified arguments.
        '''
        answer_values = subprocess.check_output([setup_file, *args])
        answer_values = answer_values.decode('utf-8')
    
        answers = answer_values.split('\n')
        for answer in answers:
            self.logger.info(answer)
    
        res = answers[-2].split(' ')[-1]
        return self.is_setup_done(res)

    def is_setup_done(self, res: str) -> bool:
        '''
        Checks if a bash script returns Done.
        '''
        if res != "DONE": 
            self.logger.error("ERROR. Failed to start service.")
            return False
        return True
    
    def prepare_redis_server(self):
        '''
        Runs a setup script for the Redis server.
        '''
        return self.run_setup_script(
            REDIS_SETUP_SH_FILE, [COMMON_BASH_LOG_FILE])
    
    def prepare_celery_worker(self):
        '''
        Runs a setup script for the Celery worker.
        '''
        return self.run_setup_script(
            CELERY_SETUP_SH_FILE, [COMMON_BASH_LOG_FILE])
        
        
#--Finish functional block