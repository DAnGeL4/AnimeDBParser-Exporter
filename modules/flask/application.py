#--Start imports block
#System imports
import os
import time
import typing as typ
from flask import Flask, jsonify
from flask_session import Session

#Custom imports
from configs import settings as cfg
from modules.flask.routes import routes
from modules.flask import service as app_service
#--Finish imports block

#--Start global constants block
app = Flask('app')
sess = Session(app)
#--Finish global constants block


#--Start functional block
@app.route(routes['index'])
def index() -> cfg.WebPage:
    '''
    Returns the primary web page.
    '''
    ss_srv = app_service.SessionService()
    render_srv = app_service.HTMLRenderingService()
    dt_srv = app_service.DataService()

    _ = ss_srv.check_common_keys()

    data = dict({
        'settings': dt_srv.get_modules_settings(),
        'parsed_titles': dt_srv.get_parsed_titles(),
        'exported_titles': dt_srv.get_exported_titles()
    })

    return render_srv.get_initial_page(data)


@app.route(routes['settingup'], methods=["POST", "GET"])
def settingup() -> cfg.JSON:
    '''
    Receives data for authorization of the user on the selected platform.
    Works only with the post method.
    '''
    req_srv = app_service.RequestService()

    if req_srv.method_is_post():
        module = req_srv.get_passed_module()
        selected_module = req_srv.get_passed_selected_module()
        cookies = req_srv.get_passed_cookies()

        ss_srv = app_service.SessionService(module=module)
        _ = ss_srv.set_filled_settings(selected_module, cookies)

        response_obj = cfg.AjaxServerResponse()
        render_srv = app_service.HTMLRenderingService()
        
        response_obj.status = cfg.ResponseStatus.FAIL
        response_obj.msg = render_srv.get_rendered_alert(
            cfg.ResponseStatus.FAIL, 'The user is not authorized.')

    return jsonify(response_obj.asdict())


@app.route(routes['action'], methods=["POST", "GET"])
def action() -> cfg.JSON:
    '''
    Runes the selected command for the selected action on the server. 
    Works only with the post method.
    '''
    cmd_srv = app_service.CommandService()
    req_srv = app_service.RequestService()
    dt_srv = app_service.DataService()

    if req_srv.method_is_post():
        action = req_srv.get_passed_action()
        cmd = req_srv.get_passed_command()
        optional_args = req_srv.get_passed_optional_args()
        module = req_srv.get_module_by_action(action)

        if not dt_srv.args_is_empty([action, cmd, optional_args, module]):
            _ = cmd_srv.init_args(action, module, optional_args)
        else:
            cmd = cfg.AjaxCommand.DEFAULT

        _ = cmd_srv.run_command(cmd)

    return jsonify(cmd_srv.get_response())

@app.route('/data_rcv', methods=["POST", "GET"])
def receive_data() -> typ.NoReturn:
    '''
    Accepts the states passed before the page was reloaded.
    '''
    req_srv = app_service.RequestService()
    ss_srv = app_service.SessionService()
    response_obj = cfg.AjaxServerResponse()
    
    response_obj.status = cfg.ResponseStatus.FAIL

    if req_srv.method_is_post():
        data = req_srv.get_passed_selects()
        module = req_srv.title_tab_module_compatibility[data['slct_pill']]

        ss_srv.set_selected_dropdown_tab(cfg.ActionModule.PARSER, data['slct_parsed_drpdwn'])
        ss_srv.set_selected_dropdown_tab(cfg.ActionModule.EXPORTER, data['slct_exported_drpdwn'])
        ss_srv.session_selected_setting_tab = module
        
        response_obj.status = cfg.ResponseStatus.DONE

    return jsonify(response_obj.asdict())
    
#--Finish functional block


#--Start main block
def run_app() -> typ.NoReturn:
    '''
    Runs the flask application.
    '''
    app.secret_key = os.environ['flask_secret_key']
    app.config['SESSION_TYPE'] = 'filesystem'

    sess.init_app(app)

    app.run(host='0.0.0.0', port=8080)
#--Finish main block
