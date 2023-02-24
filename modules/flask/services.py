#--Start imports block
#System imports
import json
import typing as typ
from jinja2 import Environment, FileSystemLoader
from pathlib import Path as PathType
from flask import request, render_template, session

#Custom imports
from configs.settings import (
    ServerAction, AjaxServerResponse, ActionModule,
    ActionToModuleCompatibility, AjaxCommand, ResponseStatus,
    TEMPLATES_DIR,
    WatchListType, AnimeByWatchList, ProcessedTitlesDump, 
    Session, Cookies, JSON, WebPagePart, WebPage
)
from configs.abstract_classes import ConnectedModuleType
from configs.application_objects import flask_cache
from configs.connected_modules import (
    EnabledParserModules, EnabledExporterModules,
    NameToModuleCompatibility, EnabledModules
)
from lib.tools import OutputLogger, is_allowed_action
from modules.web_services.web_page_tools import WebPageService, WebPageParser
from modules.web_services.web_exporter import TitleExporter
#--Finish imports block


#--Start functional block
class DataService:
    '''
    Contains methods for working 
    with data for the flask app.
    '''
    def __init__(self):
        self.logger = OutputLogger(duplicate=True, 
                                   name="data_serv").logger

    def checking_module(self, module: ConnectedModuleType, 
                        action: ServerAction) -> bool:
        '''
        Checks whether the module is allowed 
        and whether the action is enabled.
        '''
        if not is_allowed_action(action):
            self.logger.error(f"{action.name} action disabled.\n")
            return False
            
        if type(module) not in EnabledModules[action.value].value:
            self.logger.error(f"{action.name} action for module " + 
                              f"{module.module_name} are disabled.\n")
            return False
            
        return True
    
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
                                       selected_modules: typ.Dict[ServerAction, ConnectedModuleType]
                                      ) -> typ.NoReturn:
        '''Performs the specified action for the selected module.'''
        act_for_mod  = dict({
            ServerAction.PARSE: self.parse_for_selected_module,
            ServerAction.EXPORT: self.export_for_selected_module
        })
                            
        self.logger.info(f"** BEGIN PROCESSING BLOCK ({action.name}) **")
        _ = act_for_mod[action](selected_modules)
        self.logger.info(f"** END PROCESSING BLOCK ({action.name}) **\n")

    def get_parse_modules(self) -> typ.List[str]:
        '''
        Returns modules avalible for parse action.
        '''
        parse_modules = [
            module.presented_name for module in EnabledParserModules
        ]
        return parse_modules

    def get_export_modules(self) -> typ.List[str]:
        '''
        Returns modules avalible for export action.
        '''
        export_modules = [
            module.presented_name for module in EnabledExporterModules
        ]
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

    def get_parsed_titles(self) -> AnimeByWatchList:
        '''
        Returns a dump of the parsed titles.
        '''
        parsed_titles = ProcessedTitlesDump()
        return parsed_titles.asdict()

    def get_exported_titles(self) -> AnimeByWatchList:
        '''
        Returns a dump of the exported titles.
        '''
        exported_titles = ProcessedTitlesDump()
        return exported_titles.asdict()


class SessionService:
    '''
    Contains methods for working with a flask session.
    '''

    _module: ActionModule = None

    _authorized_user_key = 'username'
    _slct_platform_key = 'selected_module'
    _slct_setting_tab = 'selected_setting_tab'
    _slct_dropdown_tab = 'selected_dropdown_tab'
    _user_cookies_key = 'cookies'
    _stopped_flag = 'stopped'

    _default_watchlist = 'all'
    _html_form_keys = list([_authorized_user_key, _user_cookies_key])

    __session_structure: Session = dict({
        '_permanent': bool,
        _slct_setting_tab: ActionModule,
        ActionModule.PARSER.value: {
            _authorized_user_key: str,
            _user_cookies_key: typ.Union[str, Cookies, JSON],
            _slct_platform_key: [str, ActionModule],
            _slct_dropdown_tab: WatchListType,
            _stopped_flag: bool
        },
        ActionModule.EXPORTER.value: {
            _authorized_user_key: str,
            _user_cookies_key: typ.Union[str, Cookies, JSON],
            _slct_platform_key: [str, ActionModule],
            _slct_dropdown_tab: WatchListType,
            _stopped_flag: bool
        }
    })

    def __init__(self, module: ActionModule = None) -> typ.NoReturn:
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
    def set_stopped_flag(cls, module: ActionModule,
                         value: bool) -> typ.NoReturn:
        '''
        Sets the selected tab of the titles dropdown menu by passed module.
        '''
        session[module.value][cls._stopped_flag] = value

    @property
    def session_selected_setting_tab(self) -> str:
        '''
        The property returns the state of the selected tab 
        of the module settings.
        '''
        return session[self._slct_setting_tab]

    @session_selected_setting_tab.setter
    def session_selected_setting_tab(self,
                                     value: ActionModule) -> typ.NoReturn:
        '''
        Sets the selected tab of the module settings.
        '''
        session[self._slct_setting_tab] = value.value

    @property
    def session_selected_dropdown_tab(self) -> str:
        '''
        The property returns the state of the selected tab 
        from the titles dropdown menu.
        '''
        return session[self._module.value][self._slct_dropdown_tab]

    @session_selected_dropdown_tab.setter
    def session_selected_dropdown_tab(
            self, value: WatchListType) -> typ.NoReturn:
        '''
        Sets the selected tab of the titles dropdown menu.
        '''
        value = self._default_watchlist if value is None else value.value
        session[self._module.value][self._slct_dropdown_tab] = value

    @classmethod
    def set_selected_dropdown_tab(
            cls, module: ActionModule,
            value: [str, WatchListType]) -> typ.NoReturn:
        '''
        Sets the selected tab of the titles dropdown menu by passed module.
        '''
        value = cls._default_watchlist if value is None else value
        session[module.value][cls._slct_dropdown_tab] = value

    @classmethod
    def check_module_keys(cls) -> typ.NoReturn:
        '''
        Checks whether the modules keys
        are kept in the flask session.
        '''
        for module in ActionModule:
            if cls._slct_dropdown_tab not in session[module.value]:
                cls.set_selected_dropdown_tab(module, None)

            if cls._stopped_flag not in session[module.value]:
                cls.set_stopped_flag(module, False)

    @classmethod
    def check_html_form_keys(cls) -> typ.NoReturn:
        '''
        Checks whether the keys of html form 
        are kept in the flask session.
        '''
        dt_srv = DataService()
        for module, f_get_data in {
                ActionModule.PARSER: dt_srv.get_parse_modules,
                ActionModule.EXPORTER: dt_srv.get_export_modules
        }.items():

            if module.value not in session:
                session[module.value] = dict()

            for key in cls._html_form_keys:
                if key not in session[module.value]:
                    session[module.value][key] = ''

            if cls._slct_platform_key not in session[module.value]:
                session[module.value][cls._slct_platform_key] = f_get_data()[0]

    @classmethod
    def check_common_keys(cls) -> typ.NoReturn:
        '''
        Checks the presence of keys in the flask session.
        '''
        _ = cls.check_html_form_keys()
        _ = cls.check_module_keys()

        if cls._slct_setting_tab not in session or\
                    not session[cls._slct_setting_tab]:
            cls.session_selected_setting_tab.fset(cls, ActionModule.PARSER)

    def set_filled_settings(self, selected_module: ConnectedModuleType,
                            cookies: Cookies) -> typ.NoReturn:
        '''
        Sets the session keys for html-form - setting up.
        '''
        session[self._module.value][
            self._slct_platform_key] = selected_module.presented_name
        session[self._module.value][self._user_cookies_key] = cookies


class CacheService:
    '''
    Contains methods for working with flask cache.
    '''

    _key_parsed_titles = 'parsed_titles'
    _key_exported_titles = 'exported_titles'
    _key_proc_status = 'proc_status'
    _key_selected_parser = ActionModule.PARSER.value
    _key_selected_exporter = ActionModule.EXPORTER.value

    @property
    def cached_parsed_titles(self):
        '''
        '''
        return flask_cache.get(self._key_parsed_titles)

    @cached_parsed_titles.setter
    def cached_parsed_titles(self, value) -> typ.NoReturn:
        '''
        '''
        _ = flask_cache.set(self._key_parsed_titles, value)
    
    @property
    def cached_exported_titles(self):
        '''
        '''
        return flask_cache.get(self._key_exported_titles)
    
    @cached_exported_titles.setter
    def cached_exported_titles(self, value) -> typ.NoReturn:
        '''
        '''
        _ = flask_cache.set(self._key_exported_titles, value)

    @property
    def cached_proc_status(self):
        '''
        '''
        return flask_cache.get(self._key_proc_status)
    
    @cached_proc_status.setter
    def cached_proc_status(self, value) -> typ.NoReturn:
        '''
        '''
        _ = flask_cache.set(self._key_proc_status, value)

    @property
    def cached_parser_module(self) -> ConnectedModuleType:
        '''
        '''
        return flask_cache.get(self._key_selected_parser)
    
    @cached_parser_module.setter
    def cached_parser_module(self, value: ConnectedModuleType) -> typ.NoReturn:
        '''
        '''
        _ = flask_cache.set(self._key_selected_parser, value)

    @property
    def cached_exporter_module(self) -> ConnectedModuleType:
        '''
        '''
        return flask_cache.get(self._key_selected_exporter)
    
    @cached_exporter_module.setter
    def cached_exporter_module(self, value: ConnectedModuleType) -> typ.NoReturn:
        '''
        '''
        _ = flask_cache.set(self._key_selected_exporter, value)

    def get_cached_platform(self, module: ActionModule) -> ConnectedModuleType:
        '''
        '''
        platform = None
        if module.value is self._key_selected_parser:
            platform = self.cached_parser_module
        elif module.value is self._key_selected_exporter:
            platform = self.cached_exporter_module
        return platform

    def set_cached_platform(self, module: ActionModule, value: ConnectedModuleType) -> typ.NoReturn:
        '''
        '''
        if module.value is self._key_selected_parser:
            self.cached_parser_module = value
        elif module.value is self._key_selected_exporter:
            self.cached_exporter_module = value
                                                  

class RequestService:
    '''
    Contains methods for working with requests.
    '''

    _ajax_key_action = 'action'
    _ajax_key_module = 'module'
    _ajax_key_command = 'cmd'
    _ajax_key_cookies = 'cookies'
    _ajax_key_slct_module = 'selected_module'
    _ajax_key_slct_pill = 'selected_pill_id'
    _ajax_key_slct_parsed_drpdwn = 'selected_parsed_tab'
    _ajax_key_slct_exported_drpdwn = 'selected_exported_tab'
    _ajax_key_optional_args = 'optional_args'

    title_tab_module_compatibility = dict({
        'pills-parser-tab':
        ActionModule.PARSER,
        'pills-exporter-tab':
        ActionModule.EXPORTER,
    })

    def method_is_post(self) -> bool:
        '''
        Checks if the request method is POST.
        '''
        return request.method == "POST"

    def get_passed_action(self) -> typ.Union[ServerAction, None]:
        '''
        Returns the server action passed from jQuery ajax.
        '''
        action: str = request.form.get(self._ajax_key_action)
        try:
            action: ServerAction = ServerAction(action)
        except:
            action = None
        return action

    def get_passed_module(self) -> typ.Union[ActionModule, None]:
        '''
        Returns the action module passed from jQuery ajax.
        '''
        module: str = request.form.get(self._ajax_key_module)
        try:
            module: ActionModule = ActionModule(module)
        except:
            module = None
        return module

    def get_module_by_action(
            self,
            action: ServerAction) -> typ.Union[ActionModule, None]:
        '''
        Returns the module in accordance with the transmitted action.
        '''
        module = None
        try:
            module = ActionToModuleCompatibility[action]
        except:
            pass
        return module

    def get_passed_command(self) -> AjaxCommand:
        '''
        Returns the ajax command passed from jQuery ajax.
        '''
        cmd: str = request.form.get(self._ajax_key_command)
        try:
            cmd = AjaxCommand(cmd)
        except:
            cmd = AjaxCommand.DEFAULT
        return cmd

    def get_passed_selected_module(self) -> typ.Union[ConnectedModuleType, None]:
        '''
        Returns the selected module passed from jQuery ajax.
        '''
        selected_module = request.form.get(self._ajax_key_slct_module)
        try:
            _coincidence = NameToModuleCompatibility[selected_module]
            selected_module: ConnectedModuleType = _coincidence.value
        except:
            selected_module = None
        return selected_module

    def get_passed_cookies(self) -> typ.Union[str, Cookies, JSON]:
        '''
        Returns the user cookies passed from jQuery ajax.
        '''
        cookies = request.form.get(self._ajax_key_cookies)
        return cookies

    def get_passed_optional_args(self) -> JSON:
        '''
        Returns the optional args passed from jQuery ajax.
        '''
        optional_args = request.form.get(self._ajax_key_optional_args)
        optional_args = json.loads(optional_args)
        return optional_args

    def get_passed_selected_pill(self) -> str:
        '''
        Returns the selected pill passed from jQuery ajax.
        '''
        slct_pill_id = request.form.get(self._ajax_key_slct_pill)
        return slct_pill_id

    def get_passed_selected_parsed_dropdown(self) -> str:
        '''
        Returns the selected dropdown tab 
        for parsed titles passed from jQuery ajax.
        '''
        slct_parsed_drpdwn = request.form.get(
            self._ajax_key_slct_parsed_drpdwn)
        return slct_parsed_drpdwn

    def get_passed_selected_exported_dropdown(self) -> str:
        '''
        Returns the selected dropdown tab 
        for parsed titles exported from jQuery ajax.
        '''
        slct_exported_drpdwn = request.form.get(
            self._ajax_key_slct_exported_drpdwn)
        return slct_exported_drpdwn

    def get_passed_selects(self) -> typ.Dict[str, str]:
        '''
        Returns the selected tabs passed from jQuery ajax.
        '''
        data = dict({
            'slct_pill':
            self.get_passed_selected_pill(),
            'slct_parsed_drpdwn':
            self.get_passed_selected_parsed_dropdown(),
            'slct_exported_drpdwn':
            self.get_passed_selected_exported_dropdown()
        })
        return data

    def set_response(self, status: ResponseStatus, message: str, 
                     response: AjaxServerResponse=None
                    ) -> AjaxServerResponse:
        '''
        Specifies the server response 
        with the selected parameters.
        '''
        render_srv = HTMLRenderingService()
        response = AjaxServerResponse() if not response else response
                         
        response.status = status
        response.msg = render_srv.get_rendered_alert(status, message)
                         
        return response


class HTMLRenderingService:
    '''
    Contains methods for renderings of html templates.
    '''

    _environment: Environment = None
    _initial_page: str = 'index.html'

    def __init__(self,
                 templates_dir: typ.Union[str, PathType] = TEMPLATES_DIR):
        file_loader = FileSystemLoader(templates_dir)
        self._environment = Environment(loader=file_loader)

    def _get_rendered_template(self, file: typ.Union[str, PathType],
                               kwargs: dict) -> WebPagePart:
        '''
        Returns the specified rendred html template.
        '''
        template = self._environment.get_template(file)
        return template.render(**kwargs)

    def get_initial_page(self, kwargs: dict) -> WebPage:
        '''
        Returns the primary web page.
        '''
        return render_template(self._initial_page, **kwargs)

    def get_rendered_titles_list(self,
                                 module: ActionModule,
                                 selected_tab: str,
                                 counter: int = None) -> WebPagePart:
        '''
        Returns the html template for the specified titles list.
        '''
        dt_srv = DataService()
        kwargs_cases = dict({
            ActionModule.PARSER: {
                'template_file': "_template_parsed_titles.html",
                'kwargs': {
                    'parsed_titles': dt_srv.get_parsed_titles(counter),
                    'selected_tab': selected_tab
                }
            },
            ActionModule.EXPORTER: {
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

    def get_rendered_alert(self, status: ResponseStatus,
                           message: str) -> WebPagePart:
        '''
        Returns the html template of alert specified by the status.
        '''
        kwargs = {'status': status.value, 'message': message}
        template_file = "_template_alert_message.html"
        return self._get_rendered_template(template_file, kwargs)

    def get_rendered_status_bar(self,
                                action: ServerAction,
                                progress_xpnd: bool,
                                counter: int = None) -> WebPagePart:
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
                    'watchlist': None,
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

    _response: AjaxServerResponse = None
    _action: ServerAction = None
    _module: ActionModule = None
    _progress_xpnd: bool = None
    _selected_tab: str = None
    _optional_args: JSON = None
    _renderer: HTMLRenderingService = None

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

    def _fail_unknown_cmd(self) -> typ.NoReturn:
        '''
        Fills the object of response in accordance with 
        the status - failure; and the reason - unknown command.
        Prepares a template for a fail alert.
        '''
        self._response.status = ResponseStatus.FAIL
        self._response.msg = self._renderer.get_rendered_alert(
            ResponseStatus.FAIL, 'Unknown command.')

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
        Prepares a templates for: sttatus alert; status bar.
        '''
        self._response.status = ResponseStatus.DONE
        self._response.msg = self._renderer.get_rendered_alert(
            ResponseStatus.INFO, 'Action started.')
        self._response.statusbar_tmpl = self._renderer.get_rendered_status_bar(
            self._action, self._progress_xpnd)

        ch_srv = CacheService()
        req_srv = RequestService()
        dt_srv = DataService()
        selected_modules = dict()
        
        for action in ServerAction:
            module = req_srv.get_module_by_action(action)
            selected_modules.update({
                action: ch_srv.get_cached_platform(module)
            })
            
        _ = dt_srv.processing_for_selected_module(self._action, selected_modules)

    def _stop_action(self) -> typ.NoReturn:
        '''
        Stops selected action.
        Returns the filled object of response 
        in accordance with the status.
        Prepares a templates for: sttatus alert; status bar.
        '''
        ss_srv = SessionService(module=self._module)
        ss_srv.session_stopped_flag = True

        self._response.status = ResponseStatus.DONE
        self._response.msg = self._renderer.get_rendered_alert(
            ResponseStatus.INFO, 'Action stopped.')
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
