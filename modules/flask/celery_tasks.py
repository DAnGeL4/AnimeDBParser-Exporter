#--Start imports block
#System imports

#Custom imports
from modules.common.application_objects import celery
from .services import ActionService
#--Finish imports block


#--Start global constants block
#--Finish global constants block


#--Start functional block
@celery.task()
def task_action_processing(*args, **kwargs) -> bool:
    '''
    Starts a long-running task to perform 
    the selected action in the background.
    '''
    dt_srv = ActionService()
    _ = dt_srv.processing_for_selected_module(*args, **kwargs)
    return "FINISHED"

#--Finish functional block