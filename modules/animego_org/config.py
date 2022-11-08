#--Start imports block
#System imports
import os
import re
import json
import typing as typ
from bs4 import BeautifulSoup
from requests.structures import CaseInsensitiveDict

#Custom imports
from configs import settings as cfg
from configs import abstract_classes as ac
#--Finish imports block


#--Start global constants block
class AnimeGoOrgConfig(ac.SiteSettings):
    '''Configuration for site animego.org.'''

    user = None
    user_num = None
    _login = ''
    _password = ''
    payload = {'username': _login, 'password': _password}

    use_proxy = True
    proxies = cfg.REQUEST_PROXIES_FORMAT
    
    url_domain = "animego.org"
    url_general = f"https://{url_domain}"
    url_login = f"{url_general}/login"
    url_search = f"{url_general}/search/anime?q="
    url_wath_lists = f"{url_general}/user/{user}/mylist/anime"
    url_type_option = ""

    url_types = dict()
    cookies = {
        "REMEMBERME": "null"
    } 
    headers = CaseInsensitiveDict([
        ("User-Agent", 
         "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0"),
        ("Accept", "application/json, text/javascript, */*; q=0.01"),
        ("Accept-Language", "ru,en-US;q=0.8,en;q=0.5,be;q=0.3"),
        ("X-Requested-With", "XMLHttpRequest"),
        ("Content-Type", "application/json")
    ])

    def __init__(self, unproc_cookies):
        cookie = self._get_coockie_by_key("REMEMBERME", unproc_cookies)
        cookies = {
            "REMEMBERME": json.dumps(cookie)
        } 
        self.cookies = cookies
        
    def make_preparing(self, web_page: cfg.WebPage) -> bool:
        '''
        Performs the initial preparation of the configuration module.
        Gets a profile identifier and corrects watchlists url.
        '''
        try:
            soup = BeautifulSoup(web_page, 'lxml')
            
            login_nav = soup.find(class_="login")
            item_profile = login_nav.find(class_="text-nowrap")
            user = item_profile.text.strip()
    
            self.user = user
            self.user_num = ''.join(map(str, map(ord, self.user)))
            self.url_wath_lists = f"{self.url_general}/users/{user}/watchlist"
            
        except:
            return False
        else:
            return True
#--Finish global constants block