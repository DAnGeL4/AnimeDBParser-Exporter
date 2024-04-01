#--Start imports block
#System imports
import subprocess
import typing as typ
from pathlib import Path

#Custom imports
from configs.settings import (
    COMMON_BASH_LOG_FILE, REDIS_SETUP_SH_FILE, 
    CELERY_SETUP_SH_FILE, CELERY_TASKS_MODULE, 
    RESTART_CELERY_WORKERS
)
from lib.types import ServerAction
from lib.proxy_checker import ProxyChecker
from lib.tools import OutputLogger, is_allowed_action
from .connected_modules import EnabledModules
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
    
    def prepare_modules_proxies(self) -> typ.NoReturn:
        '''
        Performs an proxy check 
        by enabled modules for allowed actions.
        '''
        for modules_by_action in EnabledModules:
            action = ServerAction(modules_by_action.name)
                
            self.logger.info(f"Started preparing for {action.name} modules.")
            
            if not is_allowed_action(action):
                self.logger.warning(f"{action.name} action disabled.\n")
                continue
            
            for module in modules_by_action.value:
                self.logger.info("...preparing for module - " \
                                 f"{module.module_name}.")
                
                prx_chk = ProxyChecker(module.module_name)
                _ = prx_chk.check_proxy_lists_by_modules(
                            module.config_module.url_general)
                
                self.logger.info("Preparing for module - " \
                                 f"{module.module_name} is done.")
                
            self.logger.info(f"Finished preparing for {action.name} modules.\n")

    def initial_proxy_check(self) -> typ.NoReturn:
        '''Performs an initial proxy check.'''
        self.logger.info("Started initial proxy check.\n")
        prx_chk = ProxyChecker(module_name='')
        _ = prx_chk.prepare_proxy_lists()
        self.logger.info("Finished initial proxy check.\n")

    def _is_setup_done(self, res: str) -> bool:
        '''
        Checks if a bash script returns 'Done'.
        '''
        answ = True
        if res != "DONE": 
            self.logger.error("ERROR. Failed to start service.")
            answ = False
            
        return answ
    
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
        return self._is_setup_done(res)
    
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
        args = list([
            COMMON_BASH_LOG_FILE,
            str(RESTART_CELERY_WORKERS).lower(),
            CELERY_TASKS_MODULE
        ])
        return self.run_setup_script(CELERY_SETUP_SH_FILE, args)
        
#--Finish functional block