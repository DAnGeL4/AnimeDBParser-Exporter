#--Start imports block
#System imports
import re
import urllib.parse
import typing as typ
from billiard import Queue, cpu_count
from pathlib import Path
from pydantic import AnyHttpUrl
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import Logger

#Custom imports
from configs.settings import USE_MULTITHREADS
from lib.types import (
    RequestMethod, WebPage,
    AnimeInfoType, LinkedAnimeInfoType, AnimeByWatchList,
    TitleDump, WatchListType, TitleDumpByKey
)
from lib.interfaces import (
    IConnectedModule, IDataHandler, 
    ISiteSettings, IProgressHandler
)
from lib.tools import OutputLogger, ListenerLogger
from modules.flask.handlers import DefaultDataHandler
from .web_page_tools import WebPageService, WebPageParser
#--Finish imports block


#--Start functional block
class TitleExporter:
    '''
    Contains tools for the export of titles from the dump.
    '''
    _module: IConnectedModule
    _module_name: str
    _config_mod: ISiteSettings
    _loader: IDataHandler
    _type: WatchListType
    _parser: WebPageParser
    _queue: Queue
    _logger: Logger
    _progress_handler: IProgressHandler

    def __init__(self, module: IConnectedModule, 
                 progress_handler: IProgressHandler, 
                 queue: Queue = None):
                     
        self._module = module
        self._module_name = self._module.module_name
        self._config_mod = self._module.config_module
        self._loader = DefaultDataHandler
        self._progress_handler = progress_handler
                         
        self._type = None
        self._parser = WebPageParser(self._module, self._type, 
                                     self._progress_handler)
                         
        self._queue = queue
        self._logger = OutputLogger(duplicate=True, queue=self._queue, 
                                    name="title_exp").logger
    
    def get_file_name_from_url(self, url: AnyHttpUrl) -> typ.Union[str, Path]:
        '''
        Returns the name replacing all the inappropriate 
        symbols in url.
        '''
        query = url.split('/')[-1]
        dec_query = urllib.parse.unquote(query)
        file_name = re.sub("[^a-zA-z0-9]", "_", dec_query)
        return file_name
    
    def send_request(self, url: AnyHttpUrl, 
                     method: RequestMethod=RequestMethod.GET,
                     save_page: bool=False) -> WebPage:
        '''
        Sends the selected request. 
        Returns the web page of the answer.
        '''
        file_name = self.get_file_name_from_url(url)
        
        ws = WebPageService(self._module_name, self._config_mod, self._queue)
        web_page = ws.get_web_page_file(self._type, file_name, url, 
                                        method, save_page)
        return web_page
    
    def compare_titles(self, query_title: AnimeInfoType, 
                       finded_title: LinkedAnimeInfoType) -> bool:
        '''
        Compares two titles of similar types.
        '''
        if query_title.original_name != finded_title.original_name and \
                                    query_title.name != finded_title.name:
            return False
        if query_title.type != finded_title.type:
            return False
        if query_title.year != finded_title.year:
            return False
        return True
    
    def find_title_link(self, web_page: WebPage, 
                        query_title: AnimeInfoType) -> typ.Union[AnyHttpUrl, None]:
        '''
        Searches for a link to a suitable title.
        '''
        self._logger.info("Looking for the right title...")
        anime_items_list = self._parser.parse_query_anime_list(web_page)
        
        parsed_titles = self._parser.get_parsed_titles(anime_items_list)
        for finded_title in parsed_titles:
            res = self.compare_titles(query_title, finded_title)
            if res: 
                self._logger.success("...finded.")
                return finded_title.link
                
        self._logger.error("...not finded.\n")
        return None
    
    def search_title(self, title_data: AnimeInfoType) -> WebPage:
        '''
        Searches for a suitable title and gets his web page.
        '''
        self._logger.info("Starting searching...")
        query = title_data.original_name
        enc_query = urllib.parse.quote(query)
        
        url = self._config_mod.url_search + enc_query
        web_page = self.send_request(url)
        if not web_page:
            self._logger.error("...can't get query webpage.")
            return
    
        url = self.find_title_link(web_page, title_data)
        if not url: return
            
        web_page = self.send_request(url, save_page=True)
        if not web_page:
            self._logger.error("...can't get title webpage.")
            return
        
        self._logger.success("...searching done.\n")
        return web_page

    def submit_action(self, web_page: WebPage) -> bool:
        '''
        Receives a link to the desired action 
        from the web page and sends a request to it.
        '''
        self._logger.info("Starting submitting...")
        
        action_link = self._parser.parse_action_link(web_page, self._type)
        if not action_link:
            self._logger.error("...can't get action link...")
            self._logger.error("...submitting failed.\n")
            return False
            
        url = self._config_mod.url_general + action_link
        _ = self.send_request(url, RequestMethod.POST)
        
        self._logger.success("...submitting completed.\n")
        return True

    def get_json_dump_name(self, mod_name: str, user_num: int, 
                           dump_name: typ.Union[str, Path]) -> typ.Union[str, Path]:
        '''
        Returns a new dump file name.
        '''
        json_file_name = user_num + "_" + dump_name
        dump_name = mod_name + "/" + json_file_name
        return dump_name
    
    def get_titles_dump(self, query_module: IConnectedModule) -> AnimeByWatchList:
        '''
        Receives a dump base for an anime for a user.
        '''
        self._logger.info("Getting json dump for the " + 
                          f"requested module ({query_module.module_name})...")
            
        json_dump_name = query_module.get_json_dump_name()

        data = self._loader(module_name=self._module_name, 
                            queue=self._queue,
                            dump_file_name=json_dump_name)
        _ = data.load_data()
        
        if data: self._logger.success("...dump taken.\n")
        else: self._logger.error("...could not get a dump.\n")
        return data
    
    def save_error_titles(self, error_titles) -> typ.NoReturn:
        '''
        Saves a error titles of an anime for a user to file.
        '''
        self._logger.info("Saving error titles of an anime for a user...")
            
        json_dump_name = self._module.get_json_dump_name()
                            
        data = self._loader(module_name=self._module_name, 
                            queue=self._queue,
                            dump_file_name=json_dump_name)
        _ = data.update(dict(error_titles))
        res = data.save_data()
        
        if res: self._logger.success("...error titles saved.\n")
        else: self._logger.error("...not saved.\n")
        return None

    def print_error_titles(self, error_titles: typ.Dict[str, list]) -> typ.NoReturn:
        '''
        Displays titles with failed export.
        '''
        errors = False
        for type_, titles in error_titles.items():
            if not titles: continue
            errors = True
            self._logger.error(f"Not exported titles for {type_}: {len(titles)}")

        if errors:
            _ = self.save_error_titles(error_titles)

    @ListenerLogger.send_stop_msg
    def export_selected_title(self, title_item: typ.Tuple[str, TitleDump]
                             ) -> typ.Union[str, None]:
        '''
        Exports for the selected dump of title.
        '''
        title_key, title_dump = title_item
        title_data = None
        self._logger.info(f"Starting the export of title ({title_key})...")
        
        try:
            title_data = AnimeInfoType(**title_dump)
        except:
            self._logger.error(f"Bad title data. (Key: {title_key})")
            return title_key
        
        web_page = self.search_title(title_data)
        if not web_page: return title_key
            
        res = self.submit_action(web_page)
        if not res: return title_key
            
        self._logger.info(f"...title exports are completed ({title_key}).\n")
        return None

    @ListenerLogger.listener_preparing
    def export_watchlist_in_multithreads(self, watchlist_dump: 
                                         TitleDumpByKey) -> typ.List[str]:
        '''
        Exports for a watchlist dump in multi-threads.
        '''
        error_titles = list()
        self._parser = WebPageParser(self._module, self._type, self._queue, 
                                     self._progress_handler)        
                                          
        with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
            futures = []
            
            for title_item in watchlist_dump.items():
                futures.append(
                    executor.submit(self.export_selected_title, 
                                    title_item=title_item)
                )
                
            for future in as_completed(futures):
                error_title = future.result()
                if error_title:
                    error_titles.append(error_title)
                
        return error_titles

    def export_watchlist_in_order(self, watchlist_dump: 
                                  TitleDumpByKey) -> typ.List[str]:
        '''
        Exports for a watchlist dump in one stream.
        '''
        error_titles = list()
        self._parser = WebPageParser(self._module, self._type, 
                                     self._progress_handler)
        
        for title_item in watchlist_dump.items():
            error_title = self.export_selected_title(title_item)
            if error_title:
                error_titles.append(error_title)
                
        return error_titles
    
    def export_titles_dump(self, titles_dump: AnimeByWatchList) -> typ.NoReturn:
        '''
        Exports for the dump anime-base for a user.
        '''
        error_titles = dict()

        for watchlist_name, watchlist_dump in titles_dump.items():
            watchlist_type = WatchListType(watchlist_name)
            self._type = watchlist_type
            error_titles[self._type.value] = list()
            
            if USE_MULTITHREADS:
                error_titles[self._type.value].extend(
                    self.export_watchlist_in_multithreads(watchlist_dump)
                )
            else:
                error_titles[self._type.value].extend(
                    self.export_watchlist_in_order(watchlist_dump)
                )

        _ = self.print_error_titles(error_titles)
        return
#--Finish functional block