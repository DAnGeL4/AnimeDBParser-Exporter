#--Start imports block
#System imports
from flask import session
from jinja2 import Environment, FileSystemLoader

#Custom imports	
from configs import settings as cfg
#--Finish imports block


#--Start global constants block
#--Finish global constants block


#--Start decorators block
#--Finish decorators block


#--Start functional block
def get_race_list():
    return []
    
def get_gender_list():
    return []
    
def check_session_keys():
    for mod, fu in {'parser': get_race_list, 
                    'exporter': get_gender_list
                   }.items():
        if mod not in session:
            session[mod] = dict()
            
        for key in ['username', 'cookies']:
            if key not in session[mod]:
                session[mod][key] = ''
              
        if 'selected_module' not in session[mod]:
            session[mod]['selected_module'] = fu()[0]

def get_parsed_titles():
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
  
def get_rendered_titles_list(module, selected_tab):
    file_loader = FileSystemLoader(cfg.TEMPLATES_DIR)
    env = Environment(loader=file_loader)
    kwargs = dict({})
  
    if module == "parser":
        template_file = "_template_parsed_titles.html"
        kwargs = {'parsed_titles': get_parsed_titles(),
                  'selected_tab': selected_tab}
      
    elif module == "exporter":
        template_file = "_template_exported_titles.html"
        kwargs = {'exported_titles': get_exported_titles(),
                  'selected_tab': selected_tab}
        
    template = env.get_template(template_file)
    return template.render(**kwargs)
  
def get_rendered_alert(status, message):
    file_loader = FileSystemLoader(cfg.TEMPLATES_DIR)
    env = Environment(loader=file_loader)
    kwargs = {'status': status,
              'message': message}
  
    template_file = "_template_alert_message.html"
    template = env.get_template(template_file)
  
    return template.render(**kwargs)
  
def get_rendered_status_bar(action, counter=None):
    file_loader = FileSystemLoader(cfg.TEMPLATES_DIR)
    env = Environment(loader=file_loader)
  
    kwargs = {
        'selected_tab': action,
        'tab_key': action,
        'expanded': True,
        'progress': {
            'status': True,
            'all': {
                'now': 0, 
                'max': 0},
            'current': {
                'watchlist': 'watch',
                'now': 0, 
                'max': 0}
        }
    }
  
    template_file = "_template_progress_bar.html"
    template = env.get_template(template_file)
  
    return template.render(**kwargs)
#--Finish functional block


#--Start main block
#--Finish main block


#--Start run block
#--Finish run block