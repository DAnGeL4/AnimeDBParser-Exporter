#--Start imports block
#System imports
import json
import typing as typ
from flask import session
from jinja2 import Environment, FileSystemLoader
from pathlib import Path as PathType
from flask import request, render_template

#Custom imports
from configs import settings as cfg
#--Finish imports block


#--Start functional block
def get_parse_modules() -> typ.List[str]:
    '''
    '''
    service = None
    parse_modules = []

    return parse_modules


def get_export_modules() -> typ.List[str]:
    '''
    '''
    service = None
    export_modules = []

    return export_modules


def get_modules_settings():
    '''
    '''
    progress_tmpl = dict({
        'status': False,
        'all': {
            'now': 0,
            'max': 0
        },
        'current': {
            'watchlist': None,
            'now': 0,
            'max': 0
        }
    })
    settings = dict({
        'parse_modules': get_parse_modules(),
        'export_modules': get_export_modules(),
        'parser': {
            'progress': progress_tmpl
        },
        'exporter': {
            'progress': progress_tmpl
        }
    })
    return settings


def get_parsed_titles(counter):
    '''
    '''
    parsed_titles = dict({
        'watch': dict(),
        'desired': dict(),
        'viewed': dict(),
        'abandone': dict(),
        'favorites': dict(),
        'delayed': dict(),
        'reviewed': dict(),
        'errors': dict()
    })

    return parsed_titles


def get_exported_titles():
    '''
    '''
    exported_titles = dict({
        'watch': dict(),
        'desired': dict(),
        'viewed': dict(),
        'abandone': dict(),
        'favorites': dict(),
        'delayed': dict(),
        'reviewed': dict(),
        'errors': dict()
    })

    return exported_titles


class SessionService:
    '''
    Contains methods for working with a flask session.
    '''

    _module: cfg.ActionModule = None

    _authorized_user_key = 'username'
    _selected_platform_key = 'selected_module'
    _user_cookies_key = 'cookies'
    _stopped_flag = 'stopped'

    _html_form_keys = list([_authorized_user_key, _user_cookies_key])
    _titles_keys = list(['parsed_titles', 'exported_titles'])

    def __init__(self, module: cfg.ActionModule = None) -> typ.NoReturn:
        self._module = module

    @property
    def session_username(self) -> str:
        '''
        The property returns the username of an authorized user.
        '''
        return session[self._module.value][self._authorized_user_key]

    @session_username.setter
    def session_username(self, value: str) -> typ.NoReturn:
        '''
        Sets the username of an authorized user.
        '''
        session[self._module.value][self._authorized_user_key] = value

    @property
    def session_stopped_flag(self) -> bool:
        '''
        The property returns the state of a flag stopped.
        '''
        return session[self._module.value][self._stopped_flag]

    @session_stopped_flag.setter
    def session_stopped_flag(self, value: bool) -> typ.NoReturn:
        '''
        Sets the state of a flag stopped.
        '''
        session[self._module.value][self._stopped_flag] = value

    @classmethod
    def check_titles_keys(cls) -> typ.NoReturn:
        '''
        Checks whether the titles keys 
        are kept in the flask session.
        '''
        for key in cls._titles_keys:
            if key not in session:
                session[key] = dict({})

    @classmethod
    def check_html_form_keys(cls) -> typ.NoReturn:
        '''
        Checks whether the keys of html form 
        are kept in the flask session.
        '''
        for module, f_get_data in {
                cfg.ActionModule.PARSER: get_parse_modules,
                cfg.ActionModule.EXPORTER: get_export_modules
        }.items():

            if module.value not in session:
                session[module.value] = dict()

            for key in cls._html_form_keys:
                if key not in session[module.value]:
                    session[module.value][key] = ''

            if cls._selected_platform_key not in session[module.value]:
                session[module.value][
                    cls._selected_platform_key] = f_get_data()[0]

    @classmethod
    def check_common_keys(cls) -> typ.NoReturn:
        '''
        Checks the presence of keys in the flask session.
        '''
        _ = cls.check_titles_keys()
        _ = cls.check_html_form_keys()

    def check_ask_cmd_keys(self) -> typ.NoReturn:
        '''
        Checks the presence of ASK command keys in a flask session.
        '''
        if self._stopped_flag not in session[self._module.value]:
            self.session_stopped_flag = False

    def set_filled_settings(self, selected_module: str,
                            cookies: cfg.Cookies) -> typ.NoReturn:
        '''
        Sets the session keys for html-form - setting up.
        '''
        session[self._module.value][
            self._selected_platform_key] = selected_module
        session[self._module.value][self._user_cookies_key] = cookies


class CommandService:
    '''
    Contains methods for working with server commands
    passed from JQuery Ajax.
    '''

    _response: cfg.AjaxServerResponse = None
    _action: cfg.ServerAction = None
    _module: cfg.ActionModule = None
    _progress_xpnd: bool = None
    _selected_tab: str = None
    _optional_args: cfg.JSON = None

    def init_args(self, action: cfg.ServerAction, module: cfg.ActionModule,
                  optional_args: dict) -> typ.NoReturn:
        '''
        Initializes the arguments of the instance.
        '''
        _ = self._set_response_template()
        self._action = action
        self._module = module
        self._optional_args = optional_args
        self._progress_xpnd = self._optional_args['progress_xpnd']
        self._selected_tab = self._optional_args['selected_tab']

    def _set_response_template(self) -> typ.NoReturn:
        '''
        Initializes the response with a template.
        '''
        self._response = cfg.AjaxServerResponse()

    def _fail_common(self) -> typ.NoReturn:
        '''
        Fills the object of response in accordance 
        with the status of a common failure.
        Prepares a template for a fail alert.
        '''
        self._response.status = cfg.ResponseStatus.FAIL
        self._response.msg = self._renderer.get_rendered_alert(
            cfg.ResponseStatus.FAIL, 'Something went wrong.')

    def _fail_unknown_cmd(self) -> typ.NoReturn:
        '''
        Fills the object of response in accordance with 
        the status - failure; and the reason - unknown command.
        Prepares a template for a fail alert.
        '''
        self._response.status = cfg.ResponseStatus.FAIL
        self._response.msg = self._renderer.get_rendered_alert(
            cfg.ResponseStatus.FAIL, 'Unknown command.')

    def _info_stopped(self) -> typ.NoReturn:
        '''
        Fills the object of response in accordance with 
        the status - failure; and the reason - action stopped.
        Prepares a template for: informing alert; status bar.
        '''
        self._response.status = cfg.ResponseStatus.FAIL
        self._response.msg = self._renderer.get_rendered_alert(
            cfg.ResponseStatus.INFO, 'Action stopped.')
        self._response.statusbar_tmpl = self._renderer.get_rendered_status_bar(
            self._action, self._progress_xpnd)

    def _info_processed(self) -> typ.NoReturn:
        '''
        Fills the object of response in accordance with 
        the status the processed.
        Prepares a template for: status bar; titles list.
        '''
        self._response.status = cfg.ResponseStatus.PROCESSED
        self._response.statusbar_tmpl = self._renderer.get_rendered_status_bar(
            self._action, self._progress_xpnd)
        self._response.title_tmpl = self._renderer.get_rendered_titles_list(
            self._module, self._selected_tab)

    def _done_finished(self) -> typ.NoReturn:
        '''
        Fills the object of response in accordance with 
        the status - done; and the reason - finished.
        Prepares a template for: success alert; status bar; titles list.
        '''
        self._response.status = cfg.ResponseStatus.DONE
        self._response.msg = self._renderer.get_rendered_alert(
            cfg.ResponseStatus.DONE, 'Completed.')
        self._response.statusbar_tmpl = self._renderer.get_rendered_status_bar(
            self._action, self._progress_xpnd)
        self._response.title_tmpl = self._renderer.get_rendered_titles_list(
            self._module, self._selected_tab)

    def _start_action(self) -> typ.NoReturn:
        '''
        Starts selected action.
        Returns the filled object of response 
        in accordance with the status.
        Prepares a templates for: sttatus alert; status bar.
        '''
        self._response.status = cfg.ResponseStatus.DONE
        self._response.msg = self._renderer.get_rendered_alert(
            cfg.ResponseStatus.INFO, 'Action started.')
        self._response.statusbar_tmpl = self._renderer.get_rendered_status_bar(
            self._action, self._progress_xpnd, )

    def _stop_action(self) -> typ.NoReturn:
        '''
        Stops selected action.
        Returns the filled object of response 
        in accordance with the status.
        Prepares a templates for: sttatus alert; status bar.
        '''
        ss_srv = SessionService(module=self._module)
        ss_srv.session_stopped_flag = True

        self._response.status = cfg.ResponseStatus.DONE
        self._response.msg = self._renderer.get_rendered_alert(
            cfg.ResponseStatus.INFO, 'Action stopped.')
        self._response.statusbar_tmpl = self._renderer.get_rendered_status_bar(
            self._action, self._progress_xpnd)

    def _ask_action(self) -> typ.NoReturn:
        '''
        Returns the filled object of response 
        in accordance with the state of selected action.
        '''
        ss_srv = SessionService(module=self._module)
        is_stoped = ss_srv.session_stopped_flag

        if is_stoped:
            if is_stoped:
                _ = self._info_stopped()
            else:
                _ = self._done_finished()

            ss_srv.session_stopped_flag = False

        else:
            self._info_processed()

    def run_command(self, cmd: cfg.AjaxCommand) -> typ.NoReturn:
        '''
        Runes the selected command.
        '''
        comands_compatibility = {
            cfg.AjaxCommand.START: self._start_action,
            cfg.AjaxCommand.ASK: self._ask_action,
            cfg.AjaxCommand.STOP: self._stop_action,
            cfg.AjaxCommand.DEFAULT: self._fail_unknown_cmd
        }
        selected_function = comands_compatibility[cmd]

        _ = selected_function()

    def get_response(self) -> cfg.AjaxServerResponse:
        '''
        Returns the object of response as a dictionary.
        '''
        if not self._response:
            _ = self._set_response_template()
            _ = self._fail_common()

        return self._response.asdict()


#--Finish functional block
