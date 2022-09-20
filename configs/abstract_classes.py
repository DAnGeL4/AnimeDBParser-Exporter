#--Start imports block
#System imports
import os
import typing as typ
from bs4 import BeautifulSoup
from pydantic import AnyHttpUrl
#Custom imports
from configs.settings import WebPage, AnimeInfoType
#--Finish imports block


#--Start functional block
class SiteSettings:
    '''Class-model of site configuration.'''
    
    _login = ""
    _password = ""
    payload = dict()
    
    use_proxy = False
    proxies = dict()
    
    url_domain = ""
    url_general = ""
    url_login = ""
    url_wath_lists = ""
    url_type_option = ""
    url_types = dict()
    
    cookies = dict()
    headers = dict()

    
class WebPageParserAbstract:
    '''
    Abstract class describing 
    the necessary methods and attributes.
    '''
    
    def __init__(self, parser_module: 'WebPageParserAbstract') -> typ.NoReturn:
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
        

    def _get_anime_poster(self, item: BeautifulSoup) -> AnimeInfoType.poster:
        '''Parses anime poster from the item.'''
        pass

    def _get_anime_name(self, item: BeautifulSoup) -> AnimeInfoType.name:
        '''Parses anime name from the item.'''
        pass

    def _get_anime_original_name(self, item: BeautifulSoup) -> AnimeInfoType.original_name:
        '''Parses anime original name from the item.'''
        pass

    def _get_anime_type(self, item: BeautifulSoup) -> AnimeInfoType.type:
        '''Parses anime type from the item.'''
        pass

    def _get_anime_ep_count(self, item: BeautifulSoup) -> AnimeInfoType.ep_count:
        '''Parses anime episodes count from the item.'''
        pass

    def _get_anime_status(self, item: BeautifulSoup) -> AnimeInfoType.status:
        '''Parses anime status from the item.'''
        pass

    def _get_anime_year(self, item: BeautifulSoup) -> AnimeInfoType.year:
        '''Parses anime year from the item.'''
        pass

    def _get_other_names(self, item: BeautifulSoup) -> AnimeInfoType.other_names:
        '''Parses anime other names from the item.'''
        pass


class ConnectedParserModuleType:
    '''Contains the submodules for a certain platform.'''
    module_name: str
    json_dump_name: typ.Union[str, os.PathLike]
    config_module: SiteSettings
    parser_module: WebPageParserAbstract
    

class ConnectedSubmitModuleType:
    '''Contains the submodules for a certain platform.'''
    module_name: str
    #json_dump_name: typ.Union[str, os.PathLike]
    config_module: SiteSettings
    #parser_module: WebPageParserAbstract
    submit_module: ''
#--Finish functional block