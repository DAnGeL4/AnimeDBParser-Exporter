#--Start imports block
#System imports
import os
import typing as typ
from flask import Flask, render_template
from flask import session, request, jsonify

#Custom imports
from modules.flask.routes import routes
from modules.flask import service as app_service
#--Finish imports block


#--Start global constants block
app = Flask('app')
app.config['SECRET_KEY'] = os.environ['flask_secret_key']
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
  
    selected_names = session['selected_names']
    removed_names = session['removed_names']
    
    settings = dict({
        'parse_modules': app_service.get_race_list(),
        'export_modules': app_service.get_gender_list()
    })

    check_session_keys()
    
    return render_template('index.html', 
                           settings=settings,
                           parsed_titles=selected_names,
                           exported_titles=removed_names)

@app.route(routes['settingup'], methods=["POST", "GET"])
def settingup():
    if request.method == "POST":
        action = request.form.get("action")
        selected_module = request.form.get("selected_module")
        cookies = request.form.get("cookies")

        session[action]['selected_module'] = selected_module
        session[action]['username'] = 'SomeUser'
        session[action]['cookies'] = cookies
      
    return jsonify({"answer": "Success",
                    "username": "SomeUser"})

@app.route("/do", methods=["POST", "GET"])
def do():
    return index()
  
#--Finish functional block

    
#--Start main block
def run_app() -> typ.NoReturn:
    '''
    Runs the flask application.
    '''
    app.run(host='0.0.0.0', port=8080)

#--Finish main block