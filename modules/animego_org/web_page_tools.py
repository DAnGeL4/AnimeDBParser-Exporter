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
    _list_all_tag = "Все"
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
    
    def get_parsed_titles(self, items_list: typ.List[BeautifulSoup]
                         ) -> typ.List[LinkedAnimeInfoType]:
        '''
        Returns the list of anime data parsed from card items.
        '''
        parsed_titles = list()
        
        for item in items_list:
            info_obj = LinkedAnimeInfoType(
                poster=None,
                name=self._parse_name_from_card(item),
                original_name=self._parse_original_name_from_card(item),
                other_names=list(),
                type=self._parse_type_from_card(item),
                ep_count=None,
                year=self._parse_year_from_card(item),
                status=None,
                link=self._parse_link_from_card(item)
            )
            parsed_titles.append(info_obj)
            
        return parsed_titles

    def parse_query_anime_list(self, web_page: WebPage) -> typ.List[BeautifulSoup]:
        '''
        Parses of a list of card items.
        '''
        soup = BeautifulSoup(web_page, 'lxml')
        
        items_anime_cards = None
        try:    
            item_amime_list = soup.find(class_='animes-grid')
            items_anime_cards = item_amime_list.find_all(class_='animes-grid-item-body')
        except:
            items_anime_cards = list()
            
        return items_anime_cards

    def parse_action_link(self, web_page: WebPage, 
                          action: WatchListType) -> AnyHttpUrl:
        '''
        Prepares the necessary link to the action 
        on the anime web page.
        '''     
        self._logger.info("Looking for the action link...")
                              
        item_action = None
        action = self._actions_compatibility[action]
                              
        if action: 
            soup = BeautifulSoup(web_page, 'lxml')
            item_list_actions = soup.find(class_='my-list')
            item_action = item_list_actions.find('span', class_='list-group-item', 
                                                 string=action)
        else:
            self._logger.error("Unknown action type.")

        action_link = None
        if item_action:
            action_link = item_action.get('data-ajax-url')
            self._logger.info("...action link finded.")
        else:
            self._logger.warning("The requested action is not active.")
            
        return action_link
        
    def _parse_original_name_from_card(self, item: BeautifulSoup) -> str:
        '''
        Parses anime original name from the card item.
        '''
        item_original_name = item.find(class_='text-gray-dark-6')
        title_original_name = item_original_name.text.strip()
        return title_original_name
    
    def _parse_name_from_card(self, item: BeautifulSoup) -> str:
        '''
        Parses anime name from the card item.
        '''
        item_name = item.find(class_='card-title')
        item_anime_link = item_name.find('a')
        title_name = item_anime_link.get('title')
        return title_name
        
    def _parse_link_from_card(self, item: BeautifulSoup) -> AnyHttpUrl:
        '''
        Parses anime link from the card item.
        '''
        item_name = item.find(class_='card-title')
        item_anime_link = item_name.find('a')
        title_link = item_anime_link.get('href')
        return title_link
        
    def _parse_type_from_card(self, item: BeautifulSoup) -> AnimeType:
        '''
        Parses anime type from the card item.
        '''
        item_type_year = item.find(class_='animes-grid-item-body-info')
        item_type = item_type_year.find(class_='text-link-gray').get('href')
        title_type = item_type.split('/')[-1]
        return self._types_compatibility[title_type]
        
    def _parse_year_from_card(self, item: BeautifulSoup) -> int:
        '''
        Parses anime year from the card item.
        '''
        item_type_year = item.find(class_='animes-grid-item-body-info')
        item_year = item_type_year.find(class_='anime-year').find('a').get('href')
        title_year = item_year.split('/')[-1]
        return title_year

    def parse_all_titles_count(self, web_page: WebPage) -> int:
        '''Getts a number with the total count of titles.'''
        self._logger.info("Parsing titles total count...")
        
        soup = BeautifulSoup(web_page, 'lxml')
        try:
            item_lists_table = soup.find(class_="card-header")
        
            item_list_all = None
            items_lists = item_lists_table.find_all('a')
            for item_list in items_lists:
                if self._list_all_tag in item_list.text:
                    item_list_all = item_list
                    
            total_text_item = item_list_all.find('span')
            titles_count = total_text_item.text.strip()
            titles_count = int(titles_count)
            
        except:
            titles_count = 0
        
        self._logger.success("...parsed.\n")
        return titles_count

    def get_typed_anime_list(self, web_page: WebPage) -> typ.Dict[str, AnyHttpUrl]:
        '''Gets an anime list by the type of watchlist. '''
        pass

    def get_anime_info(self, web_page: WebPage) -> LinkedAnimeInfoType:
        '''Returns the anime data by the keys. '''
        pass
#--Finish functional block
