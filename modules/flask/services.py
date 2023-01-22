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
class DataService:
    '''
    Contains methods for working 
    with data for the flask app.
    '''

    def args_is_empty(self, args: typ.List[typ.Any]) -> bool:
        '''
        Returns the True if at least one of the arguments is empty.
        '''
        err = False
        for arg in args:
            err = True if arg is None else False
        return err

    def get_parse_modules(self) -> typ.List[str]:
        '''
        Returns modules avalible for parse action.
        '''
        service = None
        parse_modules = []
    
        if not parse_modules:
            parse_modules = ['parser1', 'parser2']
    
        return parse_modules

    def get_export_modules(self) -> typ.List[str]:
        '''
        Returns modules avalible for export action.
        '''
        service = None
        export_modules = []
    
        if not export_modules:
            export_modules = ['exporter1', 'exporter2']
    
        return export_modules
    
    def get_modules_settings(self) -> typ.Dict[str, dict]:
        '''
        Returns the settings for the module form.
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
            'parse_modules': self.get_parse_modules(),
            'export_modules': self.get_export_modules(),
            'parser': {
                'progress': progress_tmpl
            },
            'exporter': {
                'progress': progress_tmpl
            }
        })
        return settings
    
    def get_parsed_titles(self) -> cfg.AnimeByWatchList:
        '''
        Returns a dump of the parsed titles.
        '''
        parsed_titles = cfg.ProcessedTitlesDump()
        return parsed_titles.asdict()
    
    def get_exported_titles(self) -> cfg.AnimeByWatchList:
        '''
        Returns a dump of the exported titles.
        '''
        exported_titles = cfg.ProcessedTitlesDump()
        return exported_titles.asdict()
    
    
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
        dt_srv = DataService()
        for module, f_get_data in {
                cfg.ActionModule.PARSER: dt_srv.get_parse_modules,
                cfg.ActionModule.EXPORTER: dt_srv.get_export_modules
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


class RequestService:
    '''
    Contains methods for working with requests.
    '''

    def method_is_post(self) -> bool:
        '''
        Checks if the request method is POST.
        '''
        return request.method == "POST"

    def get_passed_action(self) -> typ.Union[cfg.ServerAction, None]:
        '''
        Returns the server action passed from jQuery ajax.
        '''
        action: str = request.form.get("action")
        try:
            action: cfg.ServerAction = cfg.ServerAction(action)
        except:
            action = None
        return action

    def get_passed_module(self) -> typ.Union[cfg.ActionModule, None]:
        '''
        Returns the action module passed from jQuery ajax.
        '''
        module: str = request.form.get("module")
        try:
            module: cfg.ActionModule = cfg.ActionModule(module)
        except:
            module = None
        return module

    def get_module_by_action(self,
                             action: cfg.ServerAction
                            ) -> typ.Union[cfg.ActionModule, None]:
        '''
        Returns the module in accordance with the transmitted action.
        '''
        module = None
        try:
            module = cfg.ActionModuleCompatibility[action]
        except:
            pass
        return module

    def get_passed_command(self) -> cfg.AjaxCommand:
        '''
        Returns the ajax command passed from jQuery ajax.
        '''
        cmd: str = request.form.get("cmd")
        try:
            cmd = cfg.AjaxCommand(cmd)
        except:
            cmd = cfg.AjaxCommand.DEFAULT
        return cmd

    def get_passed_selected_module(self) -> str:
        '''
        Returns the selected module passed from jQuery ajax.
        '''
        selected_module = request.form.get("selected_module")
        return selected_module

    def get_passed_cookies(self) -> typ.Union[str, cfg.Cookies, cfg.JSON]:
        '''
        Returns the user cookies passed from jQuery ajax.
        '''
        cookies = request.form.get("cookies")
        return cookies

    def get_passed_optional_args(self) -> cfg.JSON:
        '''
        Returns the optional args passed from jQuery ajax.
        '''
        optional_args = request.form.get("optional_args")
        optional_args = json.loads(optional_args)
        return optional_args


class HTMLRenderingService:
    '''
    Contains methods for renderings of html templates.
    '''

    _environment: Environment = None
    _initial_page: str = 'index.html'

    def __init__(self,
                 templates_dir: typ.Union[str, PathType] = cfg.TEMPLATES_DIR):
        file_loader = FileSystemLoader(templates_dir)
        self._environment = Environment(loader=file_loader)

    def _get_rendered_template(self, file: typ.Union[str, PathType],
                               kwargs: dict) -> cfg.WebPagePart:
        '''
        Returns the specified rendred html template.
        '''
        template = self._environment.get_template(file)
        return template.render(**kwargs)

    def get_initial_page(self, kwargs: dict) -> cfg.WebPage:
        '''
        Returns the primary web page.
        '''
        return render_template(self._initial_page, **kwargs)

    def get_rendered_titles_list(self,
                                 module: cfg.ActionModule,
                                 selected_tab: str) -> cfg.WebPagePart:
        '''
        Returns the html template for the specified titles list.
        '''
        dt_srv = DataService()
        kwargs_cases = dict({
            cfg.ActionModule.PARSER: {
                'template_file': "_template_parsed_titles.html",
                'kwargs': {
                    'parsed_titles': dt_srv.get_parsed_titles(),
                    'selected_tab': selected_tab
                }
            },
            cfg.ActionModule.EXPORTER: {
                'template_file': "_template_exported_titles.html",
                'kwargs': {
                    'exported_titles': dt_srv.get_exported_titles(),
                    'selected_tab': selected_tab
                }
            }
        })

        template_file = kwargs_cases[module]['template_file']
        kwargs = kwargs_cases[module]['kwargs']
        return self._get_rendered_template(template_file, kwargs)

    def get_rendered_alert(self, status: cfg.ResponseStatus,
                           message: str) -> cfg.WebPagePart:
        '''
        Returns the html template of alert specified by the status.
        '''
        kwargs = {'status': status.value, 'message': message}
        template_file = "_template_alert_message.html"
        return self._get_rendered_template(template_file, kwargs)

    def get_rendered_status_bar(self,
                                action: cfg.ServerAction,
                                progress_xpnd: bool) -> cfg.WebPagePart:
        '''
        Returns the html template of status bar with filled data.
        '''
        kwargs = {
            'selected_tab': action.value,
            'tab_key': action.value,
            'expanded': progress_xpnd,
            'progress': {
                'status': True,
                'all': {
                    'now': 0,
                    'max': 0
                },
                'current': {
                    'watchlist': 'watch',
                    'now': 0,
                    'max': 0
                }
            }
        }

        template_file = "_template_progress_bar.html"
        return self._get_rendered_template(template_file, kwargs)


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
    _renderer: HTMLRenderingService = None

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
        self._renderer = HTMLRenderingService()

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
            self._action, self._progress_xpnd)

        #Some actions

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

        #Some actions

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
