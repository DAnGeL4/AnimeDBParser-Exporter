#--Start imports block
#System imports
import typing as typ
from flask import jsonify

#Custom imports
from lib.types import (
    WebPage, JSON, ResponseStatus, 
    AjaxCommand, AjaxServerResponse, ActionModule
)
from lib.tools import is_empty_args
from modules.common.application_objects import flask_app
from .routes import routes
from .services import (
    SessionService, HTMLRenderingService,
    ActionService, RequestService, CacheService
)
from .command_service import CommandService
#--Finish imports block


#--Start global constants block
#--Finish global constants block


#--Start functional block
@flask_app.route(routes['index'])
def index() -> WebPage:
    '''
    Returns the primary web page.
    '''
    ss_srv = SessionService()
    render_srv = HTMLRenderingService()
    act_srv = ActionService()

    _ = ss_srv.check_common_keys()

    data = dict({
        'settings': act_srv.get_modules_settings(),
        'parsed_titles': act_srv.get_processed_titles(ActionModule.PARSER),
        'exported_titles': act_srv.get_processed_titles(ActionModule.EXPORTER)
    })
    
    return render_srv.get_initial_page(data)
    

@flask_app.route(routes['settingup'], methods=["POST", "GET"])
def settingup() -> JSON:
    '''
    Receives data for authorization of the user on the selected platform.
    Works only with the post method.
    '''
    req_srv = RequestService()
    if req_srv.method_is_post():
        response = req_srv.set_response(
            ResponseStatus.DONE, 'User authorized.')
        
        module = req_srv.get_passed_module()
        selected_module_cls = req_srv.get_passed_selected_module()
        cookies = req_srv.get_passed_cookies()

        if is_empty_args([module, selected_module_cls, cookies]):
            response = req_srv.set_response(
                ResponseStatus.FAIL, 'Incorrect data.')

        if response.status is not ResponseStatus.FAIL:
            act_srv = ActionService()
            ch_srv = CacheService()
            selected_module = selected_module_cls(cookies=cookies)
            
            ss_srv = SessionService(module=module)
            _ = ss_srv.set_filled_settings(selected_module, cookies)
            
            res = act_srv.prepare_module(module=selected_module)
            if res:
                _ = ch_srv.set_cached_platform(module, selected_module)
                _ = ss_srv.session_username = selected_module.config_module.username
            else:
                response = req_srv.set_response(
                    ResponseStatus.FAIL, 'The user is not authorized.')
            
    else:
        response = req_srv.set_response(
            ResponseStatus.FAIL, 'Incorrect method.')

    return jsonify(response.asdict())
    

@flask_app.route(routes['action'], methods=["POST", "GET"])
def action() -> JSON:
    '''
    Runes the selected command for the selected action on the server. 
    Works only with the post method.
    '''
    cmd_srv = CommandService()
    req_srv = RequestService()

    if req_srv.method_is_post():
        action = req_srv.get_passed_action()
        cmd = req_srv.get_passed_command()
        optional_args = req_srv.get_passed_optional_args()
        module = req_srv.get_module_by_action(action)

        if not is_empty_args([action, cmd, optional_args, module]):
            _ = cmd_srv.init_args(action, module, optional_args)
        else:
            cmd = AjaxCommand.DEFAULT

        _ = cmd_srv.run_command(cmd)

    return jsonify(cmd_srv.get_response())

@flask_app.route('/data_rcv', methods=["POST", "GET"])
def receive_data() -> typ.NoReturn:
    '''
    Accepts the states passed before the page was reloaded.
    '''
    req_srv = RequestService()
    ss_srv = SessionService()
    response_obj = AjaxServerResponse()
    
    response_obj.status = ResponseStatus.FAIL

    if req_srv.method_is_post():
        data = req_srv.get_passed_selects()
        module = req_srv.title_tab_module_compatibility[data['slct_pill']]

        _ = ss_srv.set_selected_dropdown_tab(ActionModule.PARSER, 
                                             data['slct_parsed_drpdwn'])
        _ = ss_srv.set_selected_dropdown_tab(ActionModule.EXPORTER, 
                                             data['slct_exported_drpdwn'])
        ss_srv.session_selected_setting_tab = module
        
        response_obj.status = ResponseStatus.DONE

    return jsonify(response_obj.asdict())
#--Finish functional block


#--Start main block
def run_app() -> typ.NoReturn:
    '''
    Entry point in the flask application.
    Runs the flask application.
    '''
    flask_app.run(host='0.0.0.0', port=8080)

#--Finish main block
