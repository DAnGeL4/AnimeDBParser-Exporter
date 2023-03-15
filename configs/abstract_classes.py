#--Start imports block
#System imports
import os
import re
import json
import typing as typ
from bs4 import BeautifulSoup
from pydantic import AnyHttpUrl, Protocol
from requests.structures import CaseInsensitiveDict
from logging import Logger

#Custom imports
from .settings import (
    WebPage, AnimeInfoType, LinkedAnimeInfoType, 
    WatchListType, AnimeType, AnimeStatuse, 
    JSON, Cookies
)
#--Finish imports block


#--Start functional block
class ISiteSettings:
    '''Class-model of site configuration.'''

    username: str = None
    user_num: typ.Union[str, int] = None
    _login: str = ""
    _password: str = ""
    payload: typ.Dict[str, str] = dict()
    
    use_proxy: bool = False
    proxies: typ.Dict[Protocol, AnyHttpUrl] = dict()
    
    url_domain: AnyHttpUrl = ""
    url_general: AnyHttpUrl = ""
    url_login: AnyHttpUrl = ""
    url_search: AnyHttpUrl = ""
    url_profile: AnyHttpUrl = ""
    url_wath_lists: AnyHttpUrl = ""
    url_type_option: str = ""
    url_types: typ.Dict[WatchListType, str] = dict()

    
    _cookies_key: str = ""
    
    cookies:typ.Dict[str, Cookies] = dict()
    headers: CaseInsensitiveDict = dict()

    def __init__(self, unproc_cookies: typ.Union[str, Cookies, JSON]) -> typ.NoReturn:
        cookie = self._get_coockie_by_key(self._cookies_key, unproc_cookies)
        cookies = {
            self._cookies_key: json.dumps(cookie)
        } 
        self.cookies = cookies

    def _get_coockie_by_key(self, key: str, cookies: typ.Union[str, Cookies, JSON]
                           ) -> typ.Union[Cookies, None]:
        '''
        Returns cookie from a string or json.
        '''        
        if not cookies: return None
        cookies = json.dumps(cookies)
        
        start_i = cookies.find(key)
        if start_i == -1: return cookies[1:-1]
            
        end_i = start_i + len(key)
        if cookies[end_i] == '=':
            start_i = end_i + 1
            cookies = cookies[start_i:]
            cookies = re.search("\w+", cookies)
            return cookies.group()
            
        else:
            cookies = json.loads(cookies)
            for item in cookies:
                if 'name' not in item: return None
                    
                if item['name'] == key:
                    return item['value']
                    
        return None

    def _is_authorized_user(self):
        '''Checks if a cookie exists and if a username has been received.'''
        cls = self.__class__
        self_cookies = self.cookies[self._cookies_key]
        cls_cookies = cls.cookies[cls._cookies_key]
        
        if self.username and self_cookies != cls_cookies: 
            return True
        return False
                      
    def make_preparing(self, web_page: WebPage, **kwargs):
        '''Performs the initial preparation of the configuration module.'''
        pass

    
class IWebPageParser:
    '''
    Abstract class describing 
    the necessary methods and attributes.
    '''
    
    def __init__(self, parser_module: 'IWebPageParser') -> typ.NoReturn:
        self._url_general: AnyHttpUrl

    def get_typed_anime_list(self, web_page: WebPage) -> typ.Dict[str, AnyHttpUrl]:
        '''Gets an anime list by the type of watchlist. '''
        pass

    def get_anime_info(self, web_page: WebPage) -> AnimeInfoType:
        '''Returns the anime data by the keys. '''
        pass

    def _get_item_by_tag(self, tag: str, item_list_info: BeautifulSoup):
        '''Searches for an element by tag.'''
        pass

    def _get_anime_poster(self, item: BeautifulSoup) -> AnyHttpUrl:
        '''Parses anime poster from the item.'''
        pass

    def _get_anime_name(self, item: BeautifulSoup) -> str:
        '''Parses anime name from the item.'''
        pass

    def _get_anime_original_name(self, item: BeautifulSoup) -> str:
        '''Parses anime original name from the item.'''
        pass

    def _get_anime_type(self, item: BeautifulSoup) -> AnimeType:
        '''Parses anime type from the item.'''
        pass

    def _get_anime_genres(self, item: BeautifulSoup) -> typ.List[str]:
        '''Parses anime genres from the item.'''
        pass

    def _get_anime_ep_count(self, item: BeautifulSoup) -> typ.Union[int, None]:
        '''Parses anime episodes count from the item.'''
        pass

    def _get_anime_status(self, item: BeautifulSoup) -> AnimeStatuse:
        '''Parses anime status from the item.'''
        pass

    def _get_anime_year(self, item: BeautifulSoup) -> int:
        '''Parses anime year from the item.'''
        pass

    def _get_other_names(self, item: BeautifulSoup) -> typ.List[str]:
        '''Parses anime other names from the item.'''
        pass
    
    def parse_query_anime_list(self, web_page: WebPage) -> typ.List[BeautifulSoup]:
        '''Parses the search page to obtain a list of results.'''
        pass
        
    def get_parsed_titles(self, items_list: typ.List[BeautifulSoup]
                                 ) -> typ.List[LinkedAnimeInfoType]:
        '''Parses the anime data from the title list.'''

    def parse_action_link(self, web_page: WebPage, action: WatchListType) -> AnyHttpUrl:
        '''Parses the action link from the web page.'''


class IConnectedModule:
    '''Contains the submodules for a certain platform.'''
    presented_name: str
    module_name: str
    json_dump_name: typ.Union[str, os.PathLike]
    config_module: ISiteSettings
    parser_module: IWebPageParser

    def __init__(self, cookies: typ.Union[str, Cookies, JSON]=None):
        self.config_module = self.config_module(cookies)


class IDataHandler(dict):
    '''
    Contains methods for working with the data store.
    Simulates work with a dictionary.
    '''
    
    _logger: Logger
    _module_name: str

    def load_data(self, *args, **kwargs):
        '''
        Loads data from the source.
        The source is specified in the implementation.
        '''
        pass

    def prepare_data(self, *args, **kwargs):
        '''
        Performs preparatory data processing.
        '''
        pass
        
    def save_data(self, *args, **kwargs):
        '''
        Stores data in the destination store.
        Storage is specified in the implementation.
        '''
        pass

#--Finish functional block