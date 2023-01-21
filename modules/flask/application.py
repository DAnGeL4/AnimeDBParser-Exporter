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
    _ = app_service.check_name_lists()
  
    parsed_titles = app_service.get_parsed_titles(4)
    exported_titles = app_service.get_exported_titles()
    
    settings = dict({
        'parse_modules': app_service.get_race_list(),
        'export_modules': app_service.get_gender_list(),
        'parser' : {
            'progress': {
                'status': False,
                'all': {
                    'now': 0, 
                    'max': 0}, 
                'current': {
                    'watchlist': None,
                    'now': 0, 
                    'max': 0}
            }
        },
        'exporter': {
            'progress': {
                'status': False,
                'all': {
                    'now': 0, 
                    'max': 0}, 
                'current': {
                    'watchlist': None,
                    'now': 0, 
                    'max': 0}
            }
        } 
    })
    
    app_service.check_session_keys()
    
    return render_template('index.html', 
                           settings=settings,
                           parsed_titles=parsed_titles,
                           exported_titles=exported_titles)

@app.route(routes['settingup'], methods=["POST", "GET"])
def settingup():
    if request.method == "POST":
        action = request.form.get("action")
        selected_module = request.form.get("selected_module")
        cookies = request.form.get("cookies")

        session[action]['selected_module'] = selected_module
        session[action]['username'] = 'SomeUser'
        session[action]['cookies'] = cookies
        
    return jsonify({"status": "done", 
                    "msg": app_service.get_rendered_alert('done', 'User authorized.')})

@app.route("/action", methods=["POST", "GET"])
def action():
    act2mod = {'parse': 'parser', 
               'export': 'exporter'}
    response = {'status': '',
                'msg': '',
                'title_tmpl': '',
                'statusbar_tmpl': ''}
  
    if request.method == "POST":
        action = request.form.get("action")
        cmd = request.form.get("cmd")
        optional_args = json.loads(request.form.get("optional_args"))
        progress_xpnd: bool = optional_args['progress_xpnd']
      
        print(f"action: {action}")
        print(f"cmd: {cmd}")
        print(f"optional_args: {optional_args}")

        module = act2mod[action]
        if 'stopped' not in session[module]:
            session[module]['stopped'] = False

        if cmd == "start":
            response.update({
              'status': 'done',
              'msg': app_service.get_rendered_alert('info', 'Action started'),
              'statusbar_tmpl': 
                  app_service.get_rendered_status_bar(action, progress_xpnd)
            })
            return jsonify(response)
            
        elif cmd == 'ask':
            selected_tab = optional_args['selected_tab']
          
            if session[module]['stopped']:
                if session[module]['stopped']:
                    response.update({
                      'status': 'fail',
                      'msg': app_service.get_rendered_alert('info', 'Action stopped.'),
                      'statusbar_tmpl': 
                          app_service.get_rendered_status_bar(action, progress_xpnd)
                    })
                else:
                    response.update({
                      'status': 'done',
                      'msg': app_service.get_rendered_alert('done', 'Completed.'),
                      'title_tmpl': 
                          app_service.get_rendered_titles_list(module, selected_tab),
                      'statusbar_tmpl': 
                          app_service.get_rendered_status_bar(action, progress_xpnd)
                    })
                  
                session[module].update({
                    'stopped': False
                })
                return jsonify(response)
              
            response.update({
              'status': 'processed',
              'title_tmpl': app_service.get_rendered_titles_list(module, selected_tab),
              'statusbar_tmpl': 
                  app_service.get_rendered_status_bar(action, progress_xpnd)
            })
            return jsonify(response)

        elif cmd == "stop":
            session[module].update({
                'stopped': True
            })
            response.update({
              'status': 'done',
              'msg': app_service.get_rendered_alert('info', 'Action stopped.'),
              'statusbar_tmpl': 
                  app_service.get_rendered_status_bar(action, progress_xpnd)
            })
            return jsonify(response)
          
        else:
            response.update({
              'status': 'fail',
              'msg': app_service.get_rendered_alert('fail', 'Unkwown command.')
            })
            return jsonify(response)

    response.update({
      'status': 'fail',
      'msg': app_service.get_rendered_alert('fail', 'Something went wrong.')
    })
    return jsonify(response)
  
#--Finish functional block

    
#--Start main block
def run_app() -> typ.NoReturn:
    '''
    Runs the flask application.
    '''
    app.run(host='0.0.0.0', port=8080)

#--Finish main block