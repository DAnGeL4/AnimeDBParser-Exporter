#--Start imports block
#System imports
import os
import json
import typing as typ
from flask import Flask, render_template
from flask import session, request, jsonify
from flask_session import Session

#Custom imports
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
def index() -> str:
    '''
    '''
    _ = app_service.check_session_keys()
    
    settings = app_service.get_modules_settings()
    parsed_titles = app_service.get_parsed_titles(4)
    exported_titles = app_service.get_exported_titles()
    
    return render_template('index.html', 
                           settings=settings,
                           parsed_titles=parsed_titles,
                           exported_titles=exported_titles)

@app.route(routes['settingup'], methods=["POST", "GET"])
def settingup():
    '''
    '''
    if request.method == "POST":
        action = request.form.get("action")
        selected_module = request.form.get("selected_module")
        cookies = request.form.get("cookies")

        session[action]['selected_module'] = selected_module
        session[action]['username'] = 'SomeUser'
        session[action]['cookies'] = cookies
        
    return jsonify({"status": "done", 
                    "msg": app_service.get_rendered_alert('done', 'User authorized.')})

@app.route(routes['action'], methods=["POST", "GET"])
def action():
    '''
    '''
    cmd_srv = app_service.CommandService()
    action_module_compatibility = {
        'parse': 'parser', 
        'export': 'exporter'
    }
    comands_compatibility = {
        'start': cmd_srv.start_action,
        'ask': cmd_srv.ask_action,
        'stop': cmd_srv.stop_action,
        'default': cmd_srv.fail_unkwown_cmd
    }
    
    if request.method == "POST":
        action = request.form.get("action")
        cmd = request.form.get("cmd")
        optional_args = json.loads(request.form.get("optional_args"))
        module = action_module_compatibility[action]
        
        _ = app_service.check_ask_session_keys(module)
        _ = cmd_srv.init_args(action, module, optional_args)

        if cmd not in comands_compatibility:
            cmd = 'default'
        _ = comands_compatibility[cmd]()

    return jsonify(cmd_srv.get_response())
  
#--Finish functional block

    
#--Start main block
def run_app() -> typ.NoReturn:
    '''
    Runs the flask application.
    '''
    app.run(host='0.0.0.0', port=8080)

#--Finish main block