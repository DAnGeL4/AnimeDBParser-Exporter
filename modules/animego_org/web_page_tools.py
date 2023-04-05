#--Start imports block
#System imports
import typing as typ
from billiard import Queue
from bs4 import BeautifulSoup
from pydantic import AnyHttpUrl

#Custom imports
from lib.types import AnimeType, WatchListType, LinkedAnimeInfoType, WebPage
from lib.interfaces import IWebPageParser
from lib.tools import OutputLogger
#--Finish imports block


#--Start global constants block
#--Finish global constants block


#--Start functional block
class WebPageParser(IWebPageParser):
    '''
    The class contains methods for parsing 
    the anime information from AnimeGo.org site 
    and its transformation to a unified state.
    '''
    _types_compatibility = {
        'tv': AnimeType.TV.value,
        'movie': AnimeType.MOVIE.value,
        'ova': AnimeType.OVA.value,
        'special': AnimeType.SPECIAL.value,
        'ona': AnimeType.ONA.value,
    }
    _actions_compatibility = {
        WatchListType.WATCH: 'Смотрю',
        WatchListType.DESIRED: 'Запланировано',
        WatchListType.VIEWED: 'Просмотрено',
        WatchListType.ABANDONE: 'Брошено',
        WatchListType.FAVORITES: None,
        WatchListType.DELAYED: 'Отложено',
        WatchListType.REVIEWED: 'Пересматриваю'
    }
    
    def __init__(self, module_url_general: AnyHttpUrl,
                 queue: Queue=None) -> typ.NoReturn:
        self._queue = queue
        self._logger = OutputLogger(duplicate=True, 
                                    queue=self._queue, 
                                    name='parser_animego_org').logger
        self._url_general = module_url_general
        
    def parse_original_name_from_card(self, item: BeautifulSoup) -> str:
        '''
        Parses anime original name from the card item.
        '''
        item_original_name = item.find(class_='text-gray-dark-6')
        title_original_name = item_original_name.text.strip()
        return title_original_name
    
    def parse_name_from_card(self, item: BeautifulSoup) -> str:
        '''
        Parses anime name from the card item.
        '''
        item_name = item.find(class_='card-title')
        item_anime_link = item_name.find('a')
        title_name = item_anime_link.get('title')
        return title_name
        
    def parse_link_from_card(self, item: BeautifulSoup) -> AnyHttpUrl:
        '''
        Parses anime link from the card item.
        '''
        item_name = item.find(class_='card-title')
        item_anime_link = item_name.find('a')
        title_link = item_anime_link.get('href')
        return title_link
        
    def parse_type_from_card(self, item: BeautifulSoup) -> AnimeType:
        '''
        Parses anime type from the card item.
        '''
        item_type_year = item.find(class_='animes-grid-item-body-info')
        item_type = item_type_year.find(class_='text-link-gray').get('href')
        title_type = item_type.split('/')[-1]
        return self._types_compatibility[title_type]
        
    def parse_year_from_card(self, item: BeautifulSoup) -> int:
        '''
        Parses anime year from the card item.
        '''
        item_type_year = item.find(class_='animes-grid-item-body-info')
        item_year = item_type_year.find(class_='anime-year').find('a').get('href')
        title_year = item_year.split('/')[-1]
        return title_year
    
    def get_parsed_titles(self, items_list: typ.List[BeautifulSoup]
                         ) -> typ.List[LinkedAnimeInfoType]:
        '''
        Returns the list of anime data parsed from card items.
        '''
        parsed_titles = list()
        
        for item in items_list:
            info_obj = LinkedAnimeInfoType(
                poster=None,
                name=self.parse_name_from_card(item),
                original_name=self.parse_original_name_from_card(item),
                other_names=list(),
                type=self.parse_type_from_card(item),
                ep_count=None,
                year=self.parse_year_from_card(item),
                status=None,
                link=self.parse_link_from_card(item)
            )
            parsed_titles.append(info_obj)
            
        return parsed_titles

    def parse_query_anime_list(self, web_page: WebPage) -> typ.List[BeautifulSoup]:
        '''
        Parses of a list of card items.
        '''
        soup = BeautifulSoup(web_page, 'lxml')
        
        try:    
            item_amime_list = soup.find(class_='animes-grid')
            items_anime_cards = item_amime_list.find_all(class_='animes-grid-item-body')
            
        except:
            return list()
            
        return items_anime_cards

    def parse_action_link(self, web_page: WebPage, 
                          action: WatchListType) -> AnyHttpUrl:
        '''
        Prepares the necessary link to the action 
        on the anime web page.
        '''
        self._logger.info("Looking for the action link...")
        action = self._actions_compatibility[action]
        if not action: 
            self._logger.error("Unknown action type.")
            return
            
        soup = BeautifulSoup(web_page, 'lxml')
        item_list_actions = soup.find(class_='my-list')
        item_action = item_list_actions.find('span', class_='list-group-item', 
                                             string=action)
        if not item_action:
            self._logger.warning("The requested action is not active.")
            return
            
        action_link = item_action.get('data-ajax-url')
        self._logger.info("...action link finded.")
        return action_link
#--Finish functional block