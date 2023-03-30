#--Start imports block
#System imports
import os
import types
import inspect
import typing as typ
from billiard import Queue, cpu_count
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from pydantic import AnyHttpUrl, HttpUrl
from logging import Logger

#Custom imports
from configs.settings import (
    WEB_PAGES_DIR, RELOAD_WEB_PAGES, USE_MULTITHREADS,
    UPDATE_JSON_DUMPS, TITLES_DUMP_KEY_ERRORS,
    WatchListType, WebPage, RequestMethod
)
from lib.interfaces import (
    ISiteSettings, IWebPageParser, 
    IConnectedModule, IDataHandler, IProgressHandler
)
from lib.tools import OutputLogger, ListenerLogger
from lib.requests_connections import RequestsConnections
from modules.flask.handlers import DefaultDataHandler
#--Finish imports block


#--Start functional block
class WebPageService:
    '''
    Contains auxiliary tools for working with web pages.
    '''
    _module_name: str
    _queue: Queue
    _logger: Logger
    config_module: ISiteSettings
    url_domain: HttpUrl
    url_wath_lists: AnyHttpUrl
    dir_name: [str, Path]
    dir_path: Path

    def __init__(self,
                 module_name: str,
                 config_module: ISiteSettings,
                 queue: Queue = None):
                     
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
        self.dir_path = os.path.join(WEB_PAGES_DIR, self.dir_name)

    def _get_page_filename(self, type: WatchListType,
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

    def is_exist_web_page_file(self, type: WatchListType,
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

    def load_web_page_file(self, type: WatchListType,
                           page_filename: str) -> WebPage:
        '''
        Loads a web page from a file if it exists.
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

    def save_web_page(self, type: WatchListType, page_filename: str,
                      web_page: WebPage) -> bool:
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
        res = False
        web_page = None
        req_conn = RequestsConnections(self._module_name, self.config_module,
                                       self._queue)

        self._logger.info(
            f"Preparing the configuration module ({self._module_name})...")

        if self.config_module._is_authorized_user(): 
            self._logger.info("...user alredy authorized...")
            res = True

        if not res:
            web_page = req_conn.get_web_page(type, self.config_module.url_general,
                                             RequestMethod.GET)
            res = self.config_module.make_preparing(web_page, **kwargs)

        if not res:
            self._logger.critical("...preparing failed.\n")
        else:
            self._logger.success("...preparing done.\n")
        return res

    def get_web_page_file(self,
                          type: WatchListType,
                          page_filename: str = None,
                          url: AnyHttpUrl = None,
                          method: RequestMethod = RequestMethod.GET,
                          save_page: bool = True,
                          reload_page: bool = False) -> WebPage:
        '''
        Returns the web-page by passing all the checks.
        '''
        web_page = None
        req_conn = RequestsConnections(self._module_name, self.config_module,
                                       self._queue)
                    
        if not RELOAD_WEB_PAGES and not reload_page and \
                              self.is_exist_web_page_file(type, page_filename):
            web_page = self.load_web_page_file(type, page_filename)

        else:
            web_page = req_conn.get_web_page(type, url, method)

            if web_page and save_page:
                _ = self.save_web_page(type, page_filename, web_page)

        return web_page


class WebPageParser(IWebPageParser):
    '''
    Class wrapper for a parser class 
    for a module of a certain site.
    '''
    _module: IConnectedModule
    _module_name: str
    _config_mod: ISiteSettings
    _parser_mod: IWebPageParser
    _type: WatchListType
    _web_serv: WebPageService
    progress_handler: IProgressHandler
    data: IDataHandler

    def __init__(self,
                 module: IConnectedModule,
                 type: WatchListType,
                 progress_handler: IProgressHandler,
                 queue: Queue = None):
                     
        self._module = module
        self._module_name = module.module_name
        self._config_mod = module.config_module
        self._parser_mod = module.parser_module
        self._type = type
        self._queue = queue
        self.progress_handler = progress_handler
                     
        module_name = module.module_name
        url_general = self._config_mod.url_general
        dump_file_name = self._module.get_json_dump_name()
        
        self.data = DefaultDataHandler(module_name=module_name, 
                                       queue=self._queue,
                                       dump_file_name=dump_file_name)
        self._web_serv = WebPageService(module_name, 
                                        self._config_mod,
                                        self._queue)

        self._parser_mod.__init__(self, url_general, self._queue)
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
            error_web_pages: typ.Dict[str, AnyHttpUrl]) -> typ.NoReturn:
        '''Prints error messages for aborted web-pages.'''
        for key, url in error_web_pages.items():
            self._logger.critical(
                f"Aborted:\n* Page key: {key};\n* Page URL: {url}\n")

        self.data.prepare_data(TITLES_DUMP_KEY_ERRORS)
        self.data[TITLES_DUMP_KEY_ERRORS].update(error_web_pages)

    def _is_update_needed(self, anime_key: str) -> bool:
        '''Check the need to update the json dump.'''
        if anime_key in self.data[self._type.value]:
            self._logger.info("...record already exists...")
            if not UPDATE_JSON_DUMPS:
                self._logger.info("...canceled. Updates are not needed.\n")
                return False
        return True

    def _get_web_page(self, anime_key: str,
                      anime_url: AnyHttpUrl) -> WebPage:
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
        self, anime_item: typ.Tuple[str, AnyHttpUrl]
    ) -> typ.Union[typ.Dict[str, AnyHttpUrl], None]:
        '''Updates JSON DUMP if there is no anime info.'''
        anime_key, anime_url = anime_item

        self._logger.info(f"Updating JSON dump for key {anime_key}....")
        if not self._is_update_needed(anime_key):
            return None

        web_page = self._get_web_page(*anime_item)
        if not web_page:
            return dict({anime_key: anime_url})

        anime_info = self.get_anime_info(web_page)
        self.data[self._type.value].update({anime_key: anime_info.asdict()})
        self.progress_handler.increase_progress_curr()

        self._logger.info("...JSON dump updated.\n")
        return None

    @ListenerLogger.listener_preparing
    def get_anime_data_in_multithreads(
        self, all_anime_urls: typ.Dict[str, AnyHttpUrl]
    ) -> typ.Dict[str, AnyHttpUrl]:
        '''Gets anime data in multi-threads.'''
        error_web_pages = dict()

        with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
            futures = []

            for anime_item in all_anime_urls.items():
                futures.append(
                    executor.submit(self.get_anime_info_json,
                                    anime_item=anime_item))

            for future in as_completed(futures):
                item = future.result()
                if item: 
                    error_web_pages.update(item)

        return error_web_pages

    def get_anime_data_in_order(
        self, all_anime_urls: typ.Dict[str, AnyHttpUrl]
    ) -> typ.Dict[str, AnyHttpUrl]:
        '''Gets anime data in one stream.'''
        error_web_pages = dict()
        
        for anime_item in all_anime_urls.items():
            item = self.get_anime_info_json(anime_item)
            
            if item: 
                error_web_pages.update(item)

        return error_web_pages

    def _edit_old_data(self, 
                       all_anime_urls: typ.Dict[str, AnyHttpUrl], 
                       error_web_pages: typ.Dict[str, AnyHttpUrl]
                      ) -> typ.NoReturn:
        '''
        Removes obsolete keys.
        '''
        data_keys = self.data[self._type.value].keys()
        watchlist_keys = all_anime_urls.keys()
        error_keys = error_web_pages.keys()
        
        processed_keys = list(set(watchlist_keys) - set(error_keys))
        old_keys = list(set(data_keys) - set(processed_keys))
        
        _ = list(map(
            self.data[self._type.value].__delitem__, 
            filter(self.data[self._type.value].__contains__, old_keys))
        )

    def get_anime_data(self, web_page: WebPage) -> typ.NoReturn:
        '''Gets anime data for all links.'''
        error_web_pages = list()
        all_anime_urls = self.get_typed_anime_list(web_page)
        titles_count = len(all_anime_urls.keys())
        
        self.progress_handler.initialize_progress_curr(watch_list=self._type, 
                                                       n_max=titles_count)

        if USE_MULTITHREADS:
            error_web_pages = self.get_anime_data_in_multithreads(
                                                        all_anime_urls)
        else:
            error_web_pages = self.get_anime_data_in_order(all_anime_urls)

        _ = self._edit_old_data(all_anime_urls, error_web_pages)
        _ = self.log_parser_errors(error_web_pages)

    def parse_typed_watchlist(self) -> typ.NoReturn:
        '''Parses the data of all anime titles in a typed watchlist.'''
        web_page = self._web_serv.get_web_page_file(type=self._type, 
                                                    reload_page=True)
        if web_page is None: return

        _ = self.data.load_data()
        _ = self.data.prepare_data(self._type)
        
        _ = self.get_anime_data(web_page)

        _ = self.data.save_data()


#--Finish functional block
