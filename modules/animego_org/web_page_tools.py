#--Start imports block
#System imports
import re
import typing as typ
from billiard import Queue
from bs4 import BeautifulSoup
from pydantic import AnyHttpUrl

#Custom imports
from lib.custom_types import (
    AnimeType, WatchListType, LinkedAnimeInfoType, 
    WebPage, AnimeStatus
)
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
    _list_all: str = "Все"
    
    _tag_type: str = "Тип"
    _tag_genres: str = "Жанр"
    _tag_episodes: str = "Эпизоды"
    _tag_year: str = "Сезон"
    _tag_status: str = "Статус"
    
    _types_link_compatibility = {
        'tv': AnimeType.TV.value,
        'movie': AnimeType.MOVIE.value,
        'ova': AnimeType.OVA.value,
        'special': AnimeType.SPECIAL.value,
        'ona': AnimeType.ONA.value,
    }
    _types_info_compatibility = {
        'ТВ Сериал': AnimeType.TV.value,
        'Фильм': AnimeType.MOVIE.value,
        'OVA': AnimeType.OVA.value,
        'Спешл': AnimeType.SPECIAL.value,
        'ONA': AnimeType.ONA.value,
    }
    _default_title_status = AnimeStatus.FINISHED.value
    _statuses_compatibility = {
        'Анонс': AnimeStatus.AIRING.value,
        'Вышел': AnimeStatus.FINISHED.value,
        'Онгоинг': AnimeStatus.UPCOMING.value
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
                genres=None,
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
        return self._types_link_compatibility[title_type]
        
    def _parse_year_from_card(self, item: BeautifulSoup) -> int:
        '''
        Parses anime year from the card item.
        '''
        item_type_year = item.find(class_='animes-grid-item-body-info')
        item_year = item_type_year.find(class_='anime-year').find('a').get('href')
        title_year = item_year.split('/')[-1]
        title_year = int(title_year) if title_year else None
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
                if self._list_all in item_list.text:
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
        self._logger.info("Parsing titles list...")

        all_titles_urls = dict()
        soup = BeautifulSoup(web_page, 'lxml')
        item_table = soup.find(class_="table-responsive2").find("tbody")
        items_all_titles = item_table.find_all("tr")
            
        for item in items_all_titles:
            item_link = item.find('a', class_=None)
            cut_title_url = item_link.get("href")
            title_url = self._url_general + cut_title_url
            title_dict_key = cut_title_url.split('/')[-1]
        
            all_titles_urls[title_dict_key] = title_url

        self._logger.success("...parsed.\n")
        return all_titles_urls

    def get_anime_info(self, web_page: WebPage) -> LinkedAnimeInfoType:
        '''
        Returns the anime data by the keys.
        '''
        soup = BeautifulSoup(web_page, 'lxml')
        item_list_info = soup.find(class_="media")
        item_descr_body = item_list_info.find(class_="media-body")
        item_info = item_descr_body.find(class_="anime-info")
        
        other_names = self._get_other_names(item_descr_body)
        original_name = other_names.pop(0)
        
        info_obj = LinkedAnimeInfoType(
            poster=self._get_anime_poster(item_list_info),
            name=self._get_anime_name(item_descr_body),
            original_name=original_name,
            other_names=other_names,
            type=self._get_anime_type(item_info),
            genres=self._get_anime_genres(item_info),
            ep_count=self._get_anime_ep_count(item_info),
            year=self._get_anime_year(item_info),
            status=self._get_anime_status(item_info),
            link=self._get_link(soup)
        )
        return info_obj

    def _get_item_by_tag(self, tag: str, item: BeautifulSoup):
        '''
        Searches for an element by tag.
        '''
        item_tag = item.find("dt", string=tag)
        if not item_tag: return None
        item_val = item_tag.find_next_sibling()
        return item_val

    def _get_anime_poster(self, item: BeautifulSoup) -> AnyHttpUrl:
        '''
        Parses anime poster from the item.
        '''
        item_poster = item.find(class_='anime-poster')
        anime_poster_url = item_poster.find('img').get('src')
        return anime_poster_url

    def _get_anime_name(self, item: BeautifulSoup) -> str:
        '''
        Parses anime name from the item.
        '''
        item_title = item.find(class_="anime-title").find("h1")
        anime_name = item_title.text.strip()

        return anime_name

    def _get_other_names(self, item: BeautifulSoup) -> typ.List[str]:
        '''
        Parses anime other names from the item.
        '''
        if item is None: return list()
            
        item_title = item.find(class_="anime-title")
        item_synonyms = item_title.find(class_="anime-synonyms")
        item_names_list = item_synonyms.find_all("li")
        
        anime_other_names = list()
        for item in item_names_list:
            anime_other_names.append(
                item.text.strip()
            )

        return anime_other_names

    def _get_anime_type(self, item: BeautifulSoup) -> AnimeType:
        '''
        Parses anime type from the item.
        '''
        item_type = self._get_item_by_tag(self._tag_type, item)
        if not item_type: return None
            
        type_text = item_type.text.strip()
        title_type = self._types_info_compatibility[type_text]
        
        return title_type

    def _get_anime_genres(self, item: BeautifulSoup) -> typ.List[str]:
        '''
        Parses anime genres from the item.
        '''
        item_genres = self._get_item_by_tag(self._tag_type, item)
        if not item_genres: return None
            
        item_genres_list = item_genres.find_all('a')
        title_genres = [gnr.get("title") for gnr in item_genres_list]
        
        return title_genres

    def _get_anime_ep_count(self, item: BeautifulSoup) -> typ.Union[int, None]:
        '''
        Parses anime episodes count from the item.
        '''
        item_ep = self._get_item_by_tag(self._tag_episodes, item)
        if not item_ep: return None
        
        ep_text = item_ep.text.strip()
        ep_items = ep_text.split('/')

        ep_now = ep_items[0].strip() if len(ep_items) > 1 else None
        ep_full = ep_items[-1].strip()
        
        title_ep_count = None
        try:
            title_ep_count = int(ep_full)
        except:
            title_ep_count = int(ep_now) if ep_now else title_ep_count

        return title_ep_count

    def _get_anime_year(self, item: BeautifulSoup) -> int:
        '''
        Parses anime year from the item.
        '''
        item_year = self._get_item_by_tag(self._tag_year, item)
        if not item_year: return None
        
        year_text = item_year.find("a").text.strip()
        title_year = re.findall(r'\d+', year_text)
        title_year = int(title_year[0]) if title_year else None
        
        return title_year

    def _get_anime_status(self, item: BeautifulSoup) -> AnimeStatus:
        '''
        Parses anime status from the item.
        '''
        item_status = self._get_item_by_tag(self._tag_status, item)
        
        if item_status: 
            status_text = item_status.find("a").text.strip()
            title_status = self._statuses_compatibility[status_text]
            
        else:
            title_status = self._default_title_status
            
        return title_status

    def _get_link(self, item: BeautifulSoup) -> AnyHttpUrl:
        '''
        Parses title link from the item.
        '''
        item_head = item.find("head")
        item_link = item_head.find("link", rel='canonical')
        link = item_link.get('href')
        return link
        
#--Finish functional block
