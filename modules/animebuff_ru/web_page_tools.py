#--Start imports block
#System imports
import typing as typ
from bs4 import BeautifulSoup
from pydantic import AnyHttpUrl
#Custom imports
from configs.settings import AnimeInfoType, WebPage, AnimeTypes, AnimeStatuses
from configs.abstract_classes import WebPageParserAbstract
from modules.general.tools import OutputLogger
#--Finish imports block

#--Start functional block
class WebPageParser(WebPageParserAbstract):
    '''
    The class contains methods for parsing 
    the anime information from Animebuff.ru site 
    and its transformation to a unified state.
    '''
    
    def __init__(self, module_url_general: AnyHttpUrl) -> typ.NoReturn:
        self._logger = OutputLogger(duplicate=True).logger
        
        self._url_general = module_url_general
        
        self._type_tag = "Тип"
        self._episodes_tag = "Эпизоды"
        self._status_year_tag = "Статус"
        self._other_names_tag = "Другие названия"

    def get_typed_anime_list(self, web_page: WebPage) -> typ.Dict[str, AnyHttpUrl]:
        '''
        Gets an anime list by the type of watchlist.
        '''
        all_anime_urls = dict()
        self._logger.info("Parsing anime list...")
        
        soup = BeautifulSoup(web_page, 'lxml')
        all_anime = soup.find_all(class_="watchlist__item")

        for item in all_anime:
            item_name = item.find(class_="watchlist__name")
            
            cut_anime_url = item_name.get("href")
            anime_url = self._url_general + cut_anime_url
            anime_dict_key = cut_anime_url.split('/')[-1]

            all_anime_urls[anime_dict_key] = anime_url

        self._logger.success("...parsed.\n")
        return all_anime_urls

    def get_anime_info(self, web_page: WebPage) -> AnimeInfoType:
        '''
        Returns the anime data by the keys.
        '''
        soup = BeautifulSoup(web_page, 'lxml')
        item_list_info = soup.find(class_="anime__info-list")

        item_type = self._get_item_by_tag(self._type_tag, item_list_info)
        item_episodes = self._get_item_by_tag(self._episodes_tag, item_list_info)
        item_status_year = self._get_item_by_tag(self._status_year_tag, item_list_info)
        a_items_status_year = item_status_year.find_all('a')
        item_other_names = self._get_item_by_tag(self._other_names_tag, item_list_info)

        info_obj = AnimeInfoType(
            poster=self._get_anime_poster(soup),
            name=self._get_anime_name(soup),
            original_name=self._get_anime_original_name(soup),
            other_names=self._get_other_names(item_other_names),
            type=self._get_anime_type(item_type),
            ep_count=self._get_anime_ep_count(item_episodes),
            year=self._get_anime_year(a_items_status_year),
            status=self._get_anime_status(a_items_status_year)
        )
        
        return info_obj

    def _get_item_by_tag(self, tag: str, item_list_info: BeautifulSoup):
        '''
        Searches for an element by tag.
        '''
        item = item_list_info.find(class_="anime__info-type", string=tag)
        if item: 
            return item.parent
        return item
        

    def _get_anime_poster(self, item: BeautifulSoup) -> AnyHttpUrl:
        '''
        Parses anime poster from the item.
        '''
        item_poster = item.find(class_='anime__poster-img')
        cut_poster_url = item_poster.find('img').get('src')
        anime_poster_url = self._url_general + cut_poster_url

        return anime_poster_url

    def _get_anime_name(self, item: BeautifulSoup) -> str:
        '''
        Parses anime name from the item.
        '''
        item_title = item.find(class_="anime__title")
        anime_name = item_title.text.strip()

        return anime_name

    def _get_anime_original_name(self, item: BeautifulSoup) -> str:
        '''
        Parses anime original name from the item.
        '''
        item_other_name = item.find(class_="anime__other-names")

        child_item = item_other_name.find('span')
        if child_item: child_item.decompose()
        
        anime_original_name = item_other_name.text.strip()

        return anime_original_name

    def _get_anime_type(self, item: BeautifulSoup) -> AnimeTypes:
        '''
        Parses anime type from the item.
        '''
        type_href = item.find("a").get("href")
        anime_type = type_href.split('/')[-1]
        anime_type = 'film' if anime_type == 'polnometrazhnyi-film' else anime_type

        return anime_type

    def _get_anime_ep_count(self, item: BeautifulSoup) -> typ.Union[int, None]:
        '''
        Parses anime episodes count from the item.
        '''
        ep_str_info = item.find(class_="anime__info-value").text.strip()
        ep_items = ep_str_info.split(' ')
        
        if len(ep_items) < 2: return None
            
        ep_now = ep_str_info.split(' ')[0]
        ep_full = ep_str_info.split(' ')[-1]
        
        anime_ep_count = None
        try:
            anime_ep_count = int(ep_full)
        except:
            anime_ep_count = int(ep_now)

        return anime_ep_count

    def _get_anime_status(self, item: BeautifulSoup) -> AnimeStatuses:
        '''
        Parses anime status from the item.
        '''
        item_status = item[0]
        status_href = item_status.get('href')
        anime_status = status_href.split('/')[-1]
        
        return anime_status

    def _get_anime_year(self, item: BeautifulSoup) -> int:
        '''
        Parses anime year from the item.
        '''
        item_year = item[-1]
        year_href = item_year.get('href')
        anime_year = year_href.split('/')[-1]
        
        return anime_year

    def _get_other_names(self, item: BeautifulSoup) -> typ.List[str]:
        '''
        Parses anime other names from the item.
        '''
        if item is None: return list()
            
        item_class = 'anime__info-value'
        str_other_names = item.find(class_=item_class)            
        str_other_names = str_other_names.text.replace('\n', '')
        anime_other_names = str_other_names.split(',')
        
        for name in anime_other_names:
            index = anime_other_names.index(name)
            anime_other_names[index] = name.strip()

        return anime_other_names
        
#--Finish functional block