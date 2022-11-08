#--Start imports block
#System imports
import os
import json
from bs4 import BeautifulSoup
from requests.structures import CaseInsensitiveDict
#Custom imports
from configs import settings as cfg
from configs import abstract_classes as ac
#--Finish imports block


#--Start global constants block
class AnimeBuffRuConfig(ac.SiteSettings):
    '''Configuration for site animebuff.ru.'''

    user_num = None
    _login = os.environ['animebuff_login']
    _password = os.environ['animebuff_pwd']
    payload = {'username': _login, 'password': _password}

    use_proxy = True
    proxies = cfg.REQUEST_PROXIES_FORMAT
    
    url_domain = "animebuff.ru"
    url_general = f"https://{url_domain}"
    url_login = f"{url_general}/login"
    url_search = f"{url_general}/search?q="
    url_wath_lists = f"{url_general}/users/{user_num}/watchlist"
    url_type_option = "?type="

    url_types = {
        cfg.WatchListTypes.WATCH: 
            "%D0%A1%D0%BC%D0%BE%D1%82%D1%80%D1%8E",
        cfg.WatchListTypes.DESIRED: 
            "%D0%91%D1%83%D0%B4%D1%83%20%D1%81%D0%BC%D0%BE%D1%82%D1%80%D0%B5%D1%82%D1%8C",
        cfg.WatchListTypes.VIEWED: 
            "%D0%9F%D1%80%D0%BE%D1%81%D0%BC%D0%BE%D1%82%D1%80%D0%B5%D0%BD%D0%BE",
        cfg.WatchListTypes.ABANDONE: 
            "%D0%97%D0%B0%D0%B1%D1%80%D0%BE%D1%88%D0%B5%D0%BD%D0%BE",
        cfg.WatchListTypes.FAVORITES: 
            "%D0%98%D0%B7%D0%B1%D1%80%D0%B0%D0%BD%D0%BD%D0%BE%D0%B5"
    }

    cookies = {
        "animebuff_session": "null"
    }

    headers = CaseInsensitiveDict([
        ("Accept", 
         "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"),
        ("User-Agent", 
         "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0")
    ])

    def __init__(self, unproc_cookies):
        cookie = self._get_coockie_by_key("animebuff_session", unproc_cookies)
        cookies = {
            "animebuff_session": json.dumps(cookie)
        } 
        self.cookies = cookies

    def make_preparing(self, web_page: cfg.WebPage) -> bool:
        '''
        Performs the initial preparation of the configuration module.
        Gets a profile identifier and corrects watchlists url.
        '''
        try:
            soup = BeautifulSoup(web_page, 'lxml')
            
            user_dropdown = soup.find(class_="dropdown-content")
            profile_tag = "Профиль"
            item_profile = user_dropdown.find('a', string=profile_tag)
            profile_url = item_profile.get("href")
            user_num = profile_url.split('/')[-1]
    
            self.user_num = user_num
            self.url_wath_lists = f"{self.url_general}/users/{user_num}/watchlist"
            
        except:
            return False
        else:
            return True

#--Finish global constants block