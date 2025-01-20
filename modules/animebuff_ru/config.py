#--Start imports block
#System imports
import typing as typ
from string import Template
from bs4 import BeautifulSoup
from requests.structures import CaseInsensitiveDict

#Custom imports
from configs.settings import REQUEST_PROXIES_FORMAT
from lib.custom_types import (
    WatchListType, Cookies, JSON, RequestMethod, WebPage
)
from lib.interfaces import ISiteSettings
from lib.requests_connections import RequestsConnections
#--Finish imports block


#--Start global constants block
class AnimeBuffRuConfig(ISiteSettings):
    '''Configuration for site animebuff.ru.'''
    use_proxy = True
    proxies = REQUEST_PROXIES_FORMAT
    
    url_domain = "animebuff.ru"
    url_general = f"https://{url_domain}"
    url_login = f"{url_general}/login"
    url_search = f"{url_general}/search?q="
    url_profile = Template(f"{url_general}/users/$user_num")
    url_wath_lists = Template(f"{url_general}/users/$user_num/watchlist")
    url_type_option = "?type="

    url_types = {
        WatchListType.WATCH: 
            "%D0%A1%D0%BC%D0%BE%D1%82%D1%80%D1%8E",
        WatchListType.DESIRED: 
            "%D0%91%D1%83%D0%B4%D1%83%20%D1%81%D0%BC%D0%BE%D1%82%D1%80%D0%B5%D1%82%D1%8C",
        WatchListType.VIEWED: 
            "%D0%9F%D1%80%D0%BE%D1%81%D0%BC%D0%BE%D1%82%D1%80%D0%B5%D0%BD%D0%BE",
        WatchListType.ABANDONE: 
            "%D0%97%D0%B0%D0%B1%D1%80%D0%BE%D1%88%D0%B5%D0%BD%D0%BE",
        WatchListType.FAVORITES: 
            "%D0%98%D0%B7%D0%B1%D1%80%D0%B0%D0%BD%D0%BD%D0%BE%D0%B5",
    }

    _cookies_key = "animebuff_session"

    cookies = {
        _cookies_key: "null"
    }
    headers = CaseInsensitiveDict([
        ("Accept", 
         "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"),
        ("User-Agent", 
         "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0")
    ])

    def __init__(self, unproc_cookies: typ.Union[str, Cookies, JSON]) -> typ.NoReturn:
        _ = super().__init__(unproc_cookies=unproc_cookies)

    def _get_username(self, **kwargs) -> typ.Union[str, None]:
        '''
        Gets username from the profile page.
        '''
        assert 'module_name' in kwargs
        req_conn = RequestsConnections(kwargs['module_name'], self)
        web_page = req_conn.get_web_page(None, self.url_profile, 
                                         RequestMethod.GET)
        
        soup = BeautifulSoup(web_page, 'lxml')
        item_username = soup.find(class_="new-profile__name")
        username = item_username.text.strip()
        
        return username

    def make_preparing(self, web_page: WebPage, **kwargs) -> bool:
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

            cls = self.__class__
            self.user_num = user_num
            self.url_profile = cls.url_profile.substitute(user_num=user_num)
            self.url_wath_lists = cls.url_wath_lists.substitute(user_num=user_num)
            self.username = self._get_username(**kwargs)
            
        except:
            return False
        else:
            return True

#--Finish global constants block