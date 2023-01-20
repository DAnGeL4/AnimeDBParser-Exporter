#--Start imports block
#System imports
import os
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
def check_session_keys():
    for mod, fu in {'parser': app_service.get_race_list, 
                    'exporter': app_service.get_gender_list
                   }.items():
        if mod not in session:
            session[mod] = dict()
            
        for key in ['username', 'cookies']:
            if key not in session[mod]:
                session[mod][key] = ''
              
        if 'selected_module' not in session[mod]:
            session[mod]['selected_module'] = fu()[0]

@app.route(routes['index'])
def index() -> str:
    '''
    '''
    _ = app_service.check_name_lists()
    
    settings = dict({
        'parse_modules': app_service.get_race_list(),
        'export_modules': app_service.get_gender_list()
    })

    check_session_keys()
    
    return render_template('index.html', 
                           settings=settings,
                           parsed_titles={},
                           exported_titles={})

@app.route(routes['settingup'], methods=["POST", "GET"])
def settingup():
    if request.method == "POST":
        action = request.form.get("action")
        selected_module = request.form.get("selected_module")
        cookies = request.form.get("cookies")

        session[action]['selected_module'] = selected_module
        session[action]['username'] = 'SomeUser'
        session[action]['cookies'] = cookies
      
    return jsonify({"answer": "Success"})

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

        module = act2mod[action]
        if 'stopped' not in session[module]:
            session[module]['stopped'] = False

        if cmd == "start":
            response['status'] = 'done'
            return jsonify(response)
            
        elif cmd == 'ask':
            if session[module]['stopped'] or session[module]['ask_count'] > 3:
                if session[module]['stopped']:
                    response.update({
                      'status': 'fail',
                      'msg': 'Action stopped!'
                    })
                else:
                    response.update({
                      'status': 'done',
                      'msg': 'Completed!',
                      'title_tmpl': 'Complete'
                    })
                  
                session[module].update({
                    'stopped': False
                })
                return jsonify(response)
              
            response.update({
              'status': 'processed',
              'title_tmpl': 'Processed'
            })
            return jsonify(response)

        elif cmd == "stop":
            session[module].update({
                'stopped': True,
                'ask_count': 0
            })
            response.update({
              'status': 'done',
              'msg': 'Action stopped!'
            })
            return jsonify(response)
          
        else:
            response.update({
              'status': 'fail',
              'msg': 'Unkwown command!'
            })
            return jsonify(response)

    response.update({
      'status': 'fail',
      'msg': 'Something went wrong!'
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