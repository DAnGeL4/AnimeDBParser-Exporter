#--Start imports block
#System imports
import typing as typ
from flask import session
from jinja2 import Environment, FileSystemLoader

#Custom imports	
from configs import settings as cfg
#--Finish imports block


#--Start functional block
def get_race_list():
    return []
    
def get_gender_list():
    return []

def check_ask_session_keys():
    pass

def get_modules_settings():
    settings = dict({
        'parse_modules': get_race_list(),
        'export_modules': get_gender_list(),
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
    return settings
    
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

    
class CommandService:

    def __init__(self, action, module, optional_args):
        self.action = action
        self.module = module
        self.progress_xpnd = optional_args['progress_xpnd']
        self.selected_tab = optional_args['selected_tab']
        self.response = {
            'status': '',
            'msg': '',
            'title_tmpl': '',
            'statusbar_tmpl': ''
        }
    
    def fail_unknown_cmd(self) -> typ.NoReturn:
        self.response.update({
          'status': 'fail',
          'msg': get_rendered_alert('fail', 'Unkwown command.')
        })

    def start_action(self) -> typ.NoReturn:
        self.response.update({
          'status': 'done',
          'msg': get_rendered_alert('info', 'Action started'),
          'statusbar_tmpl': 
              get_rendered_status_bar(self.action, self.progress_xpnd)
        })

    def stop_action(self) -> typ.NoReturn:
        session[self.module].update({
            'stopped': True
        })
        self.response.update({
          'status': 'done',
          'msg': get_rendered_alert('info', 'Action stopped.'),
          'statusbar_tmpl': 
              get_rendered_status_bar(self.action, self.progress_xpnd)
        })

    def ask_action(self) -> typ.NoReturn:
        if session[self.module]['stopped']:
            if session[self.module]['stopped']:
                self.response.update({
                  'status': 'fail',
                  'msg': get_rendered_alert('info', 'Action stopped.'),
                  'statusbar_tmpl': 
                      get_rendered_status_bar(self.action, self.progress_xpnd)
                })
            else:
                self.response.update({
                  'status': 'done',
                  'msg': get_rendered_alert('done', 'Completed.'),
                  'title_tmpl': 
                      get_rendered_titles_list(self.module, self.selected_tab),
                  'statusbar_tmpl': 
                      get_rendered_status_bar(self.action, self.progress_xpnd)
                })
              
            session[self.module].update({
                'stopped': False
            })
            return
          
        self.response.update({
          'status': 'processed',
          'title_tmpl': get_rendered_titles_list(self.module, self.selected_tab),
          'statusbar_tmpl': 
              get_rendered_status_bar(self.action, self.progress_xpnd)
        })
    
    def get_response(self):
        return self.response
#--Finish functional block