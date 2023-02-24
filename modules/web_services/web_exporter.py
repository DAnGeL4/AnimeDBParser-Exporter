#--Start imports block
#System imports
import re
import urllib.parse
import typing as typ
import multiprocessing as mp
from pathlib import Path
from pydantic import AnyHttpUrl
from concurrent import futures as fts

#Custom imports
from configs import settings as cfg
from configs import abstract_classes as ac
from lib.tools import OutputLogger, ListenerLogger
from modules.web_services.web_page_tools import WebPageService, WebPageParser
#--Finish imports block


#--Start functional block
class TitleExporter:
    '''
    Contains tools for the export of titles from the dump.
    '''

    def __init__(self, module: ac.ConnectedModuleType):
        self._module = module
        self._module_name = self._module.module_name
        self._config_mod = self._module.config_module
        self._parser_mod = self._module.parser_module
        self._error_titles_file = "error_titles.json"
                         
        self._type = None
        self._parser = WebPageParser(self._module, self._type)
                         
        self._queue = None
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
                     method: cfg.RequestMethod=cfg.RequestMethod.GET,
                     save_page: bool=False) -> cfg.WebPage:
        '''
        Sends the selected request. 
        Returns the web page of the answer.
        '''
        file_name = self.get_file_name_from_url(url)
        
        ws = WebPageService(self._module_name, self._config_mod, self._queue)
        web_page = ws.get_web_page_file(self._type, file_name, url, 
                                        method, save_page)
        return web_page
    
    def compare_titles(self, query_title: cfg.AnimeInfoType, 
                       finded_title: cfg.LinkedAnimeInfoType) -> bool:
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
    
    def find_title_link(self, web_page: cfg.WebPage, 
                        query_title: cfg.AnimeInfoType) -> typ.Union[AnyHttpUrl, None]:
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
    
    def search_title(self, title_data: cfg.AnimeInfoType) -> cfg.WebPage:
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

    def submit_action(self, web_page: cfg.WebPage) -> bool:
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
        _ = self.send_request(url, cfg.RequestMethod.POST)
        
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
    
    def get_titles_dump(self, query_module: ac.ConnectedModuleType) -> cfg.AnimeByWatchList:
        '''
        Receives a dump base for an anime for a user.
        '''
        mod_name = query_module.module_name
        user_num = query_module.config_module.user_num
        file_name = query_module.json_dump_name

        self._logger.info("Getting json dump for the " + 
                          f"requested module ({mod_name})...")
            
        json_dump_name = self.get_json_dump_name(mod_name, user_num, file_name)
                            
        web_serv = WebPageService(self._module_name, self._config_mod)
        json_data = web_serv.load_json_data(mod_name, json_dump_name)
        
        if json_data: self._logger.success("...dump taken.\n")
        return json_data    
    
    def save_error_titles(self, error_titles) -> typ.NoReturn:
        '''
        Saves a error titles of an anime for a user to file.
        '''
        mod_name = self._module_name
        user_num = self._config_mod.user_num
        file_name = self._error_titles_file

        self._logger.info("Saving error titles of an anime for a user...")
            
        json_dump_name = self.get_json_dump_name(mod_name, user_num, file_name)
                            
        web_serv = WebPageService(self._module_name, self._config_mod)
        json_data = web_serv.save_data_to_json(mod_name, json_dump_name, 
                                               error_titles)
        
        if json_data: self._logger.success("...error titles saved.\n")
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
    def export_selected_title(self, title_item: typ.Tuple[str, cfg.TitleDump]
                             ) -> typ.Union[str, None]:
        '''
        Exports for the selected dump of title.
        '''
        title_key, title_dump = title_item
        title_data = None
        self._logger.info(f"Starting the export of title ({title_key})...")
        
        try:
            title_data = cfg.AnimeInfoType(**title_dump)
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
                                            cfg.TitleDumpByKey) -> typ.List[str]:
        '''
        Exports for a watchlist dump in multi-threads.
        '''
        error_titles = list()
        self._parser = WebPageParser(self._module, self._type, self._queue)        
                                          
        with fts.ThreadPoolExecutor(max_workers=mp.cpu_count()) as executor:
            futures = []
            
            for title_item in watchlist_dump.items():
                futures.append(
                    executor.submit(self.export_selected_title, 
                                    title_item=title_item)
                )
                
            for future in fts.as_completed(futures):
                error_title = future.result()
                if error_title:
                    error_titles.append(error_title)
                
        return error_titles

    def export_watchlist_in_order(self, watchlist_dump: 
                                     cfg.TitleDumpByKey) -> typ.List[str]:
        '''
        Exports for a watchlist dump in one stream.
        '''
        error_titles = list()
        self._parser = WebPageParser(self._module, self._type)
        
        for title_item in watchlist_dump.items():
            error_title = self.export_selected_title(title_item)
            if error_title:
                error_titles.append(error_title)
                
        return error_titles
    
    def export_titles_dump(self, titles_dump: cfg.AnimeByWatchList) -> typ.NoReturn:
        '''
        Exports for the dump anime-base for a user.
        '''
        error_titles = dict()

        for watchlist_name, watchlist_dump in titles_dump.items():
            watchlist_type = cfg.WatchListType(watchlist_name)
            self._type = watchlist_type
            error_titles[self._type.value] = list()
            
            if cfg.USE_MULTITHREADS:
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