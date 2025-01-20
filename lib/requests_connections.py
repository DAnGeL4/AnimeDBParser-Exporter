#--Start imports block
#System imports
import cfscrape
import requests
import typing as typ
from pydantic import AnyUrl, AnyHttpUrl, IPvAnyAddress
from multiprocessing import Queue
from requests.cookies import RequestsCookieJar

#Custom imports
from .custom_types import WebPage, Session, WatchListType, RequestMethod
from .interfaces import ISiteSettings
from .proxy_checker import ProxyChecker
from .tools import OutputLogger
#--Finish imports block


#--Start functional block
class RequestsConnections(ISiteSettings):
    '''A class for working with requests connections.'''

    def __init__(self, module_name: str, config_obj: ISiteSettings, queue: Queue=None):
        self._module_name = module_name
        self._queue = queue
        _redir_out = OutputLogger(duplicate=True, queue=self._queue,
                                 name="req_con")
        self._logger = _redir_out.logger
        
        self._url_domain = config_obj.url_domain
        self._url_wath_lists = config_obj.url_wath_lists
        self._url_type_option = config_obj.url_type_option
        self._url_types = config_obj.url_types
        self._headers = config_obj.headers
        self._cookies = config_obj.cookies
        self._use_proxy = config_obj.use_proxy
        self._proxies = config_obj.proxies

        self._correct_proxies = None
    
    def get_new_session(self) -> Session:
        '''Configurings the request session object.'''
        session = requests.Session()
        session.headers = self._headers
        if self._use_proxy:
            session.proxies = self._proxies

        cookies_jar = RequestsCookieJar()
        for key, value in self._cookies.items():
            cookie = requests.cookies.create_cookie(key, value)
            cookies_jar.set_cookie(cookie)

        session.cookies = cookies_jar
        return cfscrape.create_scraper(sess=session)

    def get_correct_proxies(self) -> typ.List[AnyUrl]:
        '''
        Gets the correct proxy list if it is not loaded.
        '''
        if not self._correct_proxies:
            pw = ProxyChecker(self._module_name, self._queue)
            self._correct_proxies = pw.load_correct_proxies()

        return self._correct_proxies

    def _get_typed_url(self, type: str) -> AnyHttpUrl:
        '''Concatenates urls.'''
        if type not in self._url_types: return None
        url = self._url_wath_lists + self._url_type_option + self._url_types[type]
        return url

    def _add_arg_to_msg(self, str: str, arg: typ.Any) -> str:
        '''
        Returns a string with the argument if it is not None.
        '''
        return str + f" ({arg})" if arg else str

    def _print_error_msg(self) -> typ.NoReturn:
        '''Prints error messages.'''
        self._logger.info("-----")
        self._logger.error("Couldn't get a web page!")
        self._logger.critical("...ABORTED!\n")

    def _get_request_method(self, session: Session, 
                            method: RequestMethod) -> typ.Callable:
        '''
        Selects the desired method of sending a request.
        '''
        request_method = None
        if method is RequestMethod.GET:
            request_method = session.get
        elif method is RequestMethod.POST:
            request_method = session.post
        else:
            self._logger.error("Unknown http method.")
            return None
            
        return request_method
        
    def _get_response(self, url: AnyHttpUrl, session: Session, 
                      method: RequestMethod,
                      proxy: IPvAnyAddress=None) -> typ.Union[WebPage, None]:
        '''
        Tries to get an answer. Sends an empty request. 
        Returns None if the status code is not 200. 
        '''
        response = None
        try:
            request_method = self._get_request_method(session, method)
            response = request_method(url, timeout=2)
            
            if response.status_code == 200:
                self._logger.success(self._add_arg_to_msg("Correct response!", proxy))
                self._logger.info(f"Response: {response}\n")
            else:
                self._logger.error(self._add_arg_to_msg("Incorrect response!", proxy))
                self._logger.info(f"Response: {response}\n")
                response = None
                
        except:
            self._logger.warning(self._add_arg_to_msg("Invalid!", proxy))
            
        return response

    def _get_web_page_with_proxy(self, url: AnyHttpUrl, 
                                 method: RequestMethod) -> typ.Union[WebPage, None]:
        '''
        Gets a web-page through one of the proxies 
        from the corrected proxy list.
        '''
        response = None
        session = self.get_new_session()
        correct_proxies = self.get_correct_proxies()

        self._logger.info(f"Correct proxies: {len(correct_proxies)}\n")
        
        for proxy in correct_proxies:
            session.proxies["http"] = proxy
            session.proxies["https"] = proxy
            
            response = self._get_response(url, session, method, proxy)
            if response: break

        if not response: 
            self._print_error_msg()
            return None
                
        return response.text

    def _get_web_page_without_proxy(self, url: AnyHttpUrl, 
                                    method: RequestMethod) -> typ.Union[WebPage, None]:
        '''
        Gets a web-page without using a requests proxy.
        '''
        session = self.get_new_session()
        
        response = self._get_response(url, session, method)
        if not response: 
            self._print_error_msg()
            return None
                
        return response.text

    def get_web_page(self, type: WatchListType, url: AnyHttpUrl, 
                     method: RequestMethod) -> typ.Union[WebPage, None]: 
        '''
        Gets a web-page by parameters.
        '''
        if not url: url = self._get_typed_url(type)
        if not url: return None
            
        web_page = None
        
        self._logger.info("Trying to get correct response...")
        self._logger.info(f"Using proxy: {self._use_proxy}")
        
        if self._use_proxy:
            web_page = self._get_web_page_with_proxy(url, method)
        else:
            web_page = self._get_web_page_without_proxy(url, method)
        return web_page

#--Finish functional block