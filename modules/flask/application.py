#--Start imports block
#System imports
import os
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
app.config['SECRET_KEY'] = os.environ['flask_secret_key']
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
#--Finish global constants block


#--Start functional block
@app.route(routes['index'])
def index() -> cfg.WebPage:
    '''
    Returns the primary web page.
    '''
    _ = app_service.SessionService.check_common_keys()
    render_srv = app_service.HTMLRenderingService()

    data = dict({
        'settings': app_service.get_modules_settings(),
        'parsed_titles': app_service.get_parsed_titles(4),         #tmp func arg
        'exported_titles': app_service.get_exported_titles()
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

        #Trying to authorize the user.
        #Some actions
        #---Temporary block
        #delay imitaion
        user = 'SomeUser'
        import time
        time.sleep(4)
        #---
        
        response_obj = cfg.AjaxServerResponse()
        render_srv = app_service.HTMLRenderingService()
        
        if True:  #Temporary solution. There should be a status check
            _ = ss_srv.session_username = user
            response_obj.status = cfg.ResponseStatus.DONE
            response_obj.msg = render_srv.get_rendered_alert(
                cfg.ResponseStatus.DONE, 'User authorized.')
            
        else:
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
    
    if req_srv.method_is_post():
        action = req_srv.get_passed_action()
        cmd = req_srv.get_passed_command()
        optional_args = req_srv.get_passed_optional_args()
        module = req_srv.get_module_by_action(action)

        ss_srv = app_service.SessionService(module=module)
        
        _ = ss_srv.check_ask_cmd_keys()
        _ = cmd_srv.init_args(action, module, optional_args)
        _ = cmd_srv.run_command(cmd)

    return jsonify(cmd_srv.get_response())


#--Finish functional block


#--Start main block
def run_app() -> typ.NoReturn:
    '''
    Runs the flask application.
    '''
    app.run(host='0.0.0.0', port=8080)


#--Finish main block