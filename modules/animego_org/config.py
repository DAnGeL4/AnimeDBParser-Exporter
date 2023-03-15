#--Start imports block
#System imports
import json
import typing as typ
from string import Template
from bs4 import BeautifulSoup
from requests.structures import CaseInsensitiveDict

#Custom imports
from configs import settings as cfg
from lib import interfaces as ac
#--Finish imports block


#--Start global constants block
class AnimeGoOrgConfig(ac.ISiteSettings):
    '''Configuration for site animego.org.'''
    use_proxy = True
    proxies = cfg.REQUEST_PROXIES_FORMAT
    
    url_domain = "animego.org"
    url_general = f"https://{url_domain}"
    url_login = f"{url_general}/login"
    url_search = f"{url_general}/search/anime?q="
    url_profile = Template(f"{url_general}/user/$username")
    url_wath_lists = Template(f"{url_general}/user/$username/mylist/anime")

    _cookies_key = "REMEMBERME"
    
    cookies = {
        _cookies_key: "null"
    } 
    headers = CaseInsensitiveDict([
        ("User-Agent", 
         "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0"),
        ("Accept", "application/json, text/javascript, */*; q=0.01"),
        ("Accept-Language", "ru,en-US;q=0.8,en;q=0.5,be;q=0.3"),
        ("X-Requested-With", "XMLHttpRequest"),
        ("Content-Type", "application/json")
    ])

    def __init__(self, unproc_cookies: typ.Union[str, cfg.Cookies, cfg.JSON]) -> typ.NoReturn:
        _ = super().__init__(unproc_cookies=unproc_cookies)
        
    def make_preparing(self, web_page: cfg.WebPage, **kwargs) -> bool:
        '''
        Performs the initial preparation of the configuration module.
        Gets a profile identifier and corrects watchlists url.
        '''
        try:
            soup = BeautifulSoup(web_page, 'lxml')
            
            login_nav = soup.find(class_="login")
            item_profile = login_nav.find(class_="text-nowrap")
            username = item_profile.text.strip()

            cls = self.__class__
            self.username = username
            self.user_num = ''.join(map(str, map(ord, username)))
            self.url_profile = cls.url_profile.substitute(username=username)
            self.url_wath_lists = cls.url_wath_lists.substitute(username=username)
            
        except:
            return False
        else:
            return True
#--Finish global constants block