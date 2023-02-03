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

import subprocess

def run_setup_script(setup_file) -> typ.NoReturn:
    '''
    Checking the dependencies and external ip for atlas mongodb.
    '''
    answer_values = subprocess.check_output([setup_file])
    answer_values = answer_values.decode('utf-8')

    answers = answer_values.split('\n')
    for answer in answers:
        print(answer)

    status = answers[-2].split(' ')[-1]
    return status

def prepare_redis_server():
    '''
    '''
    redis_setup_sh_file = "./sh_scripts/redis_up.sh"
    res = run_setup_script(redis_setup_sh_file)
    
    if res != "DONE": 
        print("ERROR. Failed to start Redis.")
        return False
    return True
    
    
@basic_output
def main() -> typ.NoReturn:
    '''Entry point.'''

    res = prepare_redis_server()
    if not res: return

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

    m_serv = MainService()
    #_ = m_serv.processing_for_selected_module(selected_action, selected_modules)

    flask_app.run_app()
    
    return
        
#--Finish main block

    
#--Start run block
OutputLogger.base_configure_logging()
main()
#--Finish run block