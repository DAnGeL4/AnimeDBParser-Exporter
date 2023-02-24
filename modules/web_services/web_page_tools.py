#--Start imports block
#System imports
import os
import json
import types
import inspect
import typing as typ
import multiprocessing as mp
from concurrent import futures as fts
from pathlib import Path
from pydantic import AnyHttpUrl

#Custom imports
from configs import settings as cfg
from configs import abstract_classes as ac
from lib.tools import OutputLogger, ListenerLogger
from lib.requests_connections import RequestsConnections

#--Finish imports block


#--Start functional block
class WebPageService:
    '''
    Contains auxiliary tools for working with web pages.
    '''

    def __init__(self,
                 module_name: str,
                 config_module: ac.SiteSettings,
                 queue: mp.Queue = None):
        self._module_name = module_name
        self._queue = queue
        self._logger = OutputLogger(duplicate=True,
                                    queue=self._queue,
                                    name="web_serv"
                                   ).logger
        self.config_module = config_module

        self.url_domain = self.config_module.url_domain
        self.url_wath_lists = self.config_module.url_wath_lists

        self.dir_name = self.url_domain.replace('.', '_')
        self.dir_path = os.path.join(cfg.WEB_PAGES_DIR, self.dir_name)

    def _get_page_filename(self, type: cfg.WatchListType,
                           page_filename: str) -> str:
        '''
        Gets the file name by the type of user watchlist.
        '''
        file_name = ""
        if page_filename:
            file_name = page_filename + ".html"
        else:
            file_name = "_".join(self.url_wath_lists.split('/')[3:]) + \
                        "_" + type.value + ".html"
        return file_name

    def _get_filepath(self, file_name: str) -> Path:
        '''
        Gets the path for the file name for the dir of the web-pages.
        '''
        file_path = os.path.join(self.dir_path, file_name)
        return file_path

    def is_exist_web_page_file(self, type: cfg.WatchListType,
                               page_filename: str) -> bool:
        '''Checks if the web-page file is exist.'''
        file_name = self._get_page_filename(type, page_filename)
        file_path = self._get_filepath(file_name)

        is_exist = os.path.exists(file_path)
        if is_exist:
            self._logger.info(f"Web-page file exist. ({file_name})")
        else:
            self._logger.warning(f"Web-page file not exist. ({file_name})")

        return is_exist

    def load_web_page_file(self, type: cfg.WatchListType,
                           page_filename: str) -> cfg.WebPage:
        '''
        '''
        web_page = None
        file_name = self._get_page_filename(type, page_filename)
        file_path = self._get_filepath(file_name)
        self._logger.info(f"Loading web-page file \"{file_name}\"...")

        try:
            with open(file_path, 'r') as file:
                web_page = file.read()

            self._logger.success("...loaded.\n")
            if not web_page:
                self._logger.error("...error. File is empty.\n")

        except:
            self._logger.error("...error.\n")

        return web_page

    def save_web_page(self, type: cfg.WatchListType, page_filename: str,
                      web_page: cfg.WebPage) -> bool:
        '''
        Saves the html-response of web-page to the file.
        '''
        file_name = self._get_page_filename(type, page_filename)
        file_path = self._get_filepath(file_name)

        if not os.path.exists(self.dir_path):
            self._logger.info(
                f"Directory \"{self.dir_name}\" not exists. Creating...")
            try:
                os.mkdir(self.dir_path)
                self._logger.success("...done.")
            except:
                self._logger.error("...error.")
                return False

        self._logger.info(f"Saving the html-response to \"{file_name}\"...")
        try:
            with open(file_path, 'w') as file:
                file.write(str(web_page))
            self._logger.success("...saved.")
        except:
            self._logger.error("...error.")
            return False

        return True

    def get_preparing(self, **kwargs) -> bool:
        '''
        Performs the starting preparation of the configuration module.
        '''
        web_page = None
        req_conn = RequestsConnections(self._module_name, self.config_module,
                                       self._queue)

        self._logger.info(
            f"Preparing the configuration module ({self._module_name})...")

        web_page = req_conn.get_web_page(type, self.config_module.url_general,
                                         cfg.RequestMethod.GET)
        res = self.config_module.make_preparing(web_page, **kwargs)

        if not res:
            self._logger.critical("...preparing failed.\n")
        else:
            self._logger.success("...preparing done.\n")
        return res

    def get_web_page_file(self,
                          type: cfg.WatchListType,
                          page_filename: str = None,
                          url: AnyHttpUrl = None,
                          method: cfg.RequestMethod = cfg.RequestMethod.GET,
                          save_page: bool = True) -> cfg.WebPage:
        '''
        Returns the web-page by passing all the checks.
        '''
        web_page = None
        req_conn = RequestsConnections(self._module_name, self.config_module,
                                       self._queue)

        if self.is_exist_web_page_file(
                type, page_filename) and not cfg.RELOAD_WEB_PAGES:
            web_page = self.load_web_page_file(type, page_filename)

        else:
            web_page = req_conn.get_web_page(type, url, method)

            if web_page and save_page:
                _ = self.save_web_page(type, page_filename, web_page)

        return web_page

    def load_json_data(self, module_name: str,
                       json_dump_name: str) -> typ.Dict[str, typ.Any]:
        '''
        Loads JSON data from a file for a specific module.
        '''
        json_data = None
        file_path = os.path.join(cfg.JSON_DUMPS_DIR, json_dump_name)

        self._logger.info(f"Loading json dump for {module_name} module...")
        try:
            with open(file_path) as file:
                json_data = json.load(file)
        except:
            self._logger.error("...error.")
            return None

        if not json_data:
            self._logger.error("...error.")
            return None

        self._logger.success("...loaded.")
        return json_data

    def prepare_json_data(self, json_data: typ.Dict[str, typ.Any],
                          type: cfg.WatchListType) -> typ.Dict[str, typ.Any]:
        '''
        Prepares data into a valid format for JSON.
        '''
        json_data = dict() if not json_data else json_data
        if not type.value in json_data:
            json_data[type.value] = dict()

        return json_data

    def save_data_to_json(self, module_name: str, json_dump_name: str,
                          json_data: typ.Dict[str, typ.Any]) -> bool:
        '''
        Saves anime data in JSON format to a file 
        for a specific module.
        '''
        file_path = os.path.join(cfg.JSON_DUMPS_DIR, json_dump_name)
        json_object = json.dumps(json_data, indent=4, ensure_ascii=False)

        self._logger.info(f"Saving json dump for {module_name} module...")

        try:
            with open(file_path, 'w') as file:
                file.write(json_object)
        except:
            self._logger.error("...error.")
            return False

        self._logger.success("...saved.")
        return True


class WebPageParser(ac.WebPageParserAbstract):
    '''
    Class wrapper for a parser class 
    for a module of a certain site.
    '''

    def __init__(self,
                 module: ac.ConnectedModuleType,
                 type: cfg.WatchListType,
                 queue: mp.Queue = None):
        self._module = module
        self._config_mod = module.config_module
        self._parser_mod = module.parser_module

        self._type = type
        self._queue = queue
        self._mg_url = self._config_mod.url_general
        self._module_name = module.module_name
        self._web_serv = WebPageService(self._module_name, self._config_mod,
                                        self._queue)

        json_file_name = self._config_mod.user_num + "_" +\
                                            self._module.json_dump_name
        self._json_dump_name = self._module_name + "/" + json_file_name

        self._parser_mod.__init__(self, self._mg_url, self._queue)
        self._init_methods()

    def _init_methods(self) -> typ.NoReturn:
        '''
        Copies the methods of the implemented WebPageParserAbstract 
        child class for the common(this) child class.
        
        ! Not worked with multiprocessing tools !
        '''
        method_list = inspect.getmembers(self._parser_mod,
                                         predicate=inspect.isfunction)

        for method_name, method in method_list:
            if method_name == '__init__': continue
            typed_method = types.MethodType(method, self)
            setattr(self, method_name, typed_method)

    def log_parser_errors(
            self,
            error_web_pages: typ.List[typ.Dict[str,
                                               AnyHttpUrl]]) -> typ.NoReturn:
        '''Prints error messages for aborted web-pages.'''
        for error_page in error_web_pages:
            if error_page is None: continue
            key, url = list(error_page.items())[0]
            self._logger.critical(
                f"Aborted:\n* Page key: {key};\n* Page URL: {url}\n")

    def _is_update_needed(
            self, anime_key: str, json_data: cfg.AnimeByWatchList
    ) -> typ.Union[None, WebPageService]:
        '''Check the need to update the json dump.'''
        if anime_key in json_data[self._type.value]:
            self._logger.info("...record already exists...")
            if not cfg.UPDATE_JSON_DUMPS:
                self._logger.info("...canceled. Updates are not needed.\n")
                return False
        return True

    def _get_web_page(self, anime_key: str,
                      anime_url: AnyHttpUrl) -> cfg.WebPage:
        '''Uses the queue for logging, if necessary, and returns web_page.'''
        web_serv = self._web_serv
        if self._queue:
            web_serv = WebPageService(self._module_name, self._config_mod,
                                      self._queue)

        web_page = web_serv.get_web_page_file(self._type,
                                              page_filename=anime_key,
                                              url=anime_url)
        return web_page

    @ListenerLogger.send_stop_msg
    def get_anime_info_json(
        self, anime_item: typ.Tuple[str, AnyHttpUrl],
        json_data: cfg.AnimeByWatchList
    ) -> typ.Union[typ.Dict[str, AnyHttpUrl], None]:
        '''Updates JSON DUMP if there is no anime info.'''
        anime_key, anime_url = anime_item

        self._logger.info(f"Updating JSON dump for key {anime_key}....")
        if not self._is_update_needed(anime_key, json_data):
            return None

        web_page = self._get_web_page(*anime_item)
        if not web_page:
            return dict({anime_key: anime_url})

        anime_info = self.get_anime_info(web_page)
        json_data[self._type.value].update({anime_key: anime_info.asdict()})

        self._logger.info("...JSON dump updated.\n")
        return None

    @ListenerLogger.listener_preparing
    def get_anime_data_in_multithreads(
        self, all_anime_urls: typ.Dict[str, AnyHttpUrl],
        json_data: cfg.AnimeByWatchList
    ) -> typ.List[typ.Dict[str, AnyHttpUrl]]:
        '''Gets anime data in multi-threads.'''
        error_web_pages = list()

        with fts.ThreadPoolExecutor(max_workers=mp.cpu_count()) as executor:
            futures = []

            for anime_item in all_anime_urls.items():
                futures.append(
                    executor.submit(self.get_anime_info_json,
                                    anime_item=anime_item,
                                    json_data=json_data))

            for future in fts.as_completed(futures):
                error_web_pages.append(future.result())

        return error_web_pages

    def get_anime_data_in_order(
        self, all_anime_urls: typ.Dict[str, AnyHttpUrl],
        json_data: cfg.AnimeByWatchList
    ) -> typ.List[typ.Dict[str, AnyHttpUrl]]:
        '''Gets anime data in one stream.'''
        error_web_pages = list()
        for anime_item in all_anime_urls.items():
            error_web_pages.append(
                self.get_anime_info_json(anime_item, json_data))

        return error_web_pages

    def get_anime_data(
            self, web_page: cfg.WebPage,
            json_data: cfg.AnimeByWatchList) -> cfg.AnimeByWatchList:
        '''Gets anime data for all links.'''
        error_web_pages = list()
        all_anime_urls = self.get_typed_anime_list(web_page)

        if cfg.USE_MULTITHREADS:
            error_web_pages = self.get_anime_data_in_multithreads(
                all_anime_urls, json_data)
        else:
            error_web_pages = self.get_anime_data_in_order(
                all_anime_urls, json_data)

        self.log_parser_errors(error_web_pages)
        return json_data

    def parse_typed_watchlist(self) -> typ.NoReturn:
        '''Parses the data of all anime titles in a typed watchlist.'''
        web_page = self._web_serv.get_web_page_file(type=self._type)
        if web_page is None: return

        json_data = self._web_serv.load_json_data(self._module_name,
                                                  self._json_dump_name)
        json_data = self._web_serv.prepare_json_data(json_data, self._type)
        json_data = self.get_anime_data(web_page, json_data)

        _ = self._web_serv.save_data_to_json(self._module_name,
                                             self._json_dump_name, json_data)


#--Finish functional block
