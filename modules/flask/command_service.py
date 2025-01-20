#--Start imports block
#System imports
import typing as typ
from celery.result import AsyncResult

#Custom imports
from lib.custom_types import (
    ServerAction, AjaxServerResponse, ActionModule,
    AjaxCommand, ResponseStatus, JSON
)
from modules.common.application_objects import celery
from modules.flask import celery_tasks as cl_tasks
from .services import (
    HTMLRenderingService, CacheService, 
    RequestService, SessionService
)
#--Finish imports block


#--Start global constants block
#--Finish global constants block


#--Start functional block
class CommandService:
    '''
    Contains methods for working with server commands
    passed from JQuery Ajax.
    '''

    _response: AjaxServerResponse
    _action: ServerAction
    _module: ActionModule
    _progress_xpnd: bool
    _selected_tab: str
    _optional_args: JSON
    _renderer: HTMLRenderingService

    def init_args(self, action: ServerAction, module: ActionModule,
                  optional_args: dict) -> typ.NoReturn:
        '''
        Initializes the arguments of the instance.
        '''
        _ = self._set_response_template()
        self._renderer = HTMLRenderingService()
                      
        self._action = action
        self._module = module
        self._optional_args = optional_args
        self._progress_xpnd = self._optional_args['progress_xpnd']
        self._selected_tab = self._optional_args['selected_tab']

    def _set_response_template(self) -> typ.NoReturn:
        '''
        Initializes the response with a template.
        '''
        self._response = AjaxServerResponse()

    def _fail_common(self) -> typ.NoReturn:
        '''
        Fills the object of response in accordance 
        with the status of a common failure.
        Prepares a template for a fail alert.
        '''
        self._response.status = ResponseStatus.FAIL
        self._response.msg = self._renderer.get_rendered_alert(
            ResponseStatus.FAIL, 'Something went wrong.')

    def _fail_task(self) -> typ.NoReturn:
        '''
        Fills the object of response in accordance 
        with the status of a common failure.
        Prepares a template for a fail alert.
        '''
        self._response.status = ResponseStatus.FAIL
        self._response.msg = self._renderer.get_rendered_alert(
            ResponseStatus.FAIL, 'Action failed.')

    def _fail_unknown_cmd(self) -> typ.NoReturn:
        '''
        Fills the object of response in accordance with 
        the status - failure; and the reason - unknown command.
        Prepares a template for a fail alert.
        '''
        self._response.status = ResponseStatus.FAIL
        self._response.msg = self._renderer.get_rendered_alert(
            ResponseStatus.FAIL, 'Unknown command.')

    def _warn_not_runing(self) -> typ.NoReturn:
        '''
        Fills the object of response in accordance with 
        the status - fail; and the reason - action not running.
        Prepares a template for: status alert; status bar; titles list.
        '''
        self._response.status = ResponseStatus.FAIL
        self._response.statusbar_tmpl = self._renderer.get_rendered_status_bar(
            self._action, self._progress_xpnd)
        self._response.msg = self._renderer.get_rendered_alert(
            ResponseStatus.WARNING, 'The action is not in progress.')

    def _info_stopped(self) -> typ.NoReturn:
        '''
        Fills the object of response in accordance with 
        the status - failure; and the reason - action stopped.
        Prepares a template for: informing alert; status bar.
        '''
        self._response.status = ResponseStatus.FAIL
        self._response.msg = self._renderer.get_rendered_alert(
            ResponseStatus.INFO, 'Action stopped.')
        self._response.statusbar_tmpl = self._renderer.get_rendered_status_bar(
            self._action, self._progress_xpnd)

    def _info_processed(self) -> typ.NoReturn:
        '''
        Fills the object of response in accordance with 
        the status the processed.
        Prepares a template for: status bar; titles list.
        '''
        self._response.status = ResponseStatus.PROCESSED
        self._response.statusbar_tmpl = self._renderer.get_rendered_status_bar(
            self._action, self._progress_xpnd)
        self._response.title_tmpl = self._renderer.get_rendered_titles_list(
            self._module, self._selected_tab)

    def _done_started(self) -> typ.NoReturn:
        '''
        Fills the object of response in accordance with 
        the status - done; and the reason - started.
        Prepares a template for: status alert; status bar; titles list.
        '''
        self._response.status = ResponseStatus.DONE
        self._response.statusbar_tmpl = self._renderer.get_rendered_status_bar(
            self._action, self._progress_xpnd)
        self._response.msg = self._renderer.get_rendered_alert(
            ResponseStatus.INFO, 'Action started.')

    def _done_stopped(self) -> typ.NoReturn:
        '''
        Fills the object of response in accordance with 
        the status - done; and the reason - stopped.
        Prepares a template for: status alert; status bar; titles list.
        '''
        self._response.status = ResponseStatus.DONE
        self._response.statusbar_tmpl = self._renderer.get_rendered_status_bar(
            self._action, self._progress_xpnd)
        self._response.msg = self._renderer.get_rendered_alert(
            ResponseStatus.DONE, 'Action stopped.')

    def _done_finished(self) -> typ.NoReturn:
        '''
        Fills the object of response in accordance with 
        the status - done; and the reason - finished.
        Prepares a template for: success alert; status bar; titles list.
        '''
        self._response.status = ResponseStatus.DONE
        self._response.msg = self._renderer.get_rendered_alert(
            ResponseStatus.DONE, 'Completed.')
        self._response.statusbar_tmpl = self._renderer.get_rendered_status_bar(
            self._action, self._progress_xpnd)
        self._response.title_tmpl = self._renderer.get_rendered_titles_list(
            self._module, self._selected_tab)

    def _start_action(self) -> typ.NoReturn:
        '''
        Starts selected action.
        Returns the filled object of response 
        in accordance with the status.
        Prepares a templates for: status alert; status bar.
        '''
        ch_srv = CacheService()
        req_srv = RequestService()
        
        selected_modules = dict()
        for action in ServerAction:
            module = req_srv.get_module_by_action(action)
            selected_modules.update({
                action: ch_srv.get_cached_platform(module)
            })
        
        task = cl_tasks.task_action_processing.delay(
            self._action, selected_modules)
        ch_srv.cached_running_task = task.id
        
        if task.status == 'PENDING':
            _ = self._done_started()
        else:
            _ = self._fail_common()

    def _stop_action(self) -> typ.NoReturn:
        '''
        Stops selected celery task by action.
        Returns the filled object of response.
        '''
        ch_srv = CacheService()
        ss_srv = SessionService(module=self._module)
        
        ss_srv.session_stopped_flag = True
        task_id = ch_srv.cached_running_task
        
        if task_id is not None:
            task = AsyncResult(id=task_id, app=celery)
            _ = task.revoke(terminate=True, signal='SIGKILL')
            _ = self._done_stopped()

        else:
            _ = self._warn_not_runing()

    def _ask_action(self) -> typ.NoReturn:
        '''
        Returns the filled object of response 
        in accordance with the state of selected action.
        '''
        ss_srv = SessionService(module=self._module)
        is_stoped = ss_srv.session_stopped_flag
        
        if is_stoped:
            _ = self._info_stopped()
            ss_srv.session_stopped_flag = False

        else:
            ch_srv = CacheService()
            task_id = ch_srv.cached_running_task
            
            status = None
            if task_id is not None:
                task = AsyncResult(id=task_id, app=celery)
                status = task.status if task else None

            if status is None:
                _ = self._fail_common()
            elif status == 'REVOKED':
                _ = self._info_stopped()
            elif status == 'PENDING':
                _ = self._info_processed()
            elif status == 'SUCCESS':
                _ = self._done_finished()
            elif status == 'FAILURE':
                _ = self._fail_task()
            else:
                _ = self._fail_common()

    def run_command(self, cmd: AjaxCommand) -> typ.NoReturn:
        '''
        Runes the selected command.
        '''
        comands_compatibility = {
            AjaxCommand.START: self._start_action,
            AjaxCommand.ASK: self._ask_action,
            AjaxCommand.STOP: self._stop_action,
            AjaxCommand.DEFAULT: self._fail_unknown_cmd
        }
        selected_function = comands_compatibility[cmd]

        _ = selected_function()

    def get_response(self) -> AjaxServerResponse:
        '''
        Returns the object of response as a dictionary.
        '''
        if not self._response:
            _ = self._set_response_template()
            _ = self._fail_common()

        return self._response.asdict()

#--Finish functional block
