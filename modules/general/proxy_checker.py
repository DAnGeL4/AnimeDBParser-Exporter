#--Start imports block
#System imports
import os
import requests
import multiprocessing as mp
from pathlib import Path
import typing as typ
from functools import partial
from pydantic import IPvAnyAddress, AnyUrl
#Custom imports
from configs import settings as cfg
from modules.general.tools import OutputLogger
#--Finish imports block


#--Start functional block
class ProxyChecker:
    '''
    The class for download, checking and validate proxy lists.
    '''
    #Constant block
    #----------------------------
    local_proxy_files: Path = cfg.LOCAL_PROXY_FILES
    online_proxy_lists: Path = cfg.ONLINE_PROXY_LISTS 
    proxies: typ.Dict[str, IPvAnyAddress] = cfg.REQUEST_PROXIES_FORMAT
    url_to_check: AnyUrl = None
    _module_name: str = None
    _correct_proxy_filename: Path = None
    #----------------------------
    
    def __init__(self, module_name: str, queue: mp.Queue=None):
        self._module_name = module_name
        self._queue = queue

        filename = f"{self._module_name}_correct_proxies"
        self._correct_proxy_filename = os.path.join(cfg.PROXY_LISTS_DIR, filename)
        
        _redir_out = OutputLogger(duplicate=True, queue=self._queue, 
                                 name="proxy_chk")
        self._logger = _redir_out.logger

    def donload_proxy_lists(self) -> typ.NoReturn:
        '''
        Downloads a proxy lists from web.
        '''
        file_links = self.online_proxy_lists
        
        for file_name, link in file_links.items():
            self._logger.info(f"Downloading proxy list ({file_name})...")
            
            response = requests.get(link)
            write_filename = os.path.join(cfg.PROXY_LISTS_DIR, file_name)
            open(write_filename, 'wb').write(response.content)
            
            self._logger.success("...done.")
        self._logger.info("Downloaded.\n")

    def handler(self, proxy: IPvAnyAddress, 
                protocol: str)  -> typ.Union[AnyUrl, None]:
        '''
        Checks if the proxy address is live 
        and if the request returns a correct response.
        '''
        proxies = self.proxies
        proxies["http"] = proxies["https"] = f"{protocol}://{proxy}"
    
        try:
            response = requests.get(self.url_to_check, 
                                    proxies=proxies, 
                                    timeout=2)
            self._logger.info(f"Live proxy: {protocol}://{proxy}")
            self._logger.info(f"Response: {response}")
            
            if response.status_code == 200:
                self._logger.success("Valid proxy.\n")
                return f"{protocol}://{proxy}"
    
        except:
            self._logger.warning(f"Invalid proxy! ({proxy})")
            
        return

    def check_proxy_list(self, file: Path, protocol: str
                        ) -> typ.List[typ.Union[AnyUrl, None]]:
        '''
        Reads the files of the proxy lists 
        and checks the proxies in a multi-flow.
        '''
        data = None
        
        with open(file) as file:
            proxy_list = ''.join(file.readlines()).strip().split("\n")
        
        with mp.Pool(mp.cpu_count()) as process:
            data = process.map(partial(self.handler, protocol=protocol), proxy_list)
    
        return data

    def write_correct_proxies(self, correct_proxies: typ.List[AnyUrl]) -> typ.NoReturn:
        '''
        Writes a checked list of valid proxy to the file.
        '''
        self._logger.info("Writing correct proxy list...")

        try:
            with open(self._correct_proxy_filename, 'w') as file:
                file.write('\n'.join(correct_proxies))
            self._logger.success("...writed.\n")
        except:
            self._logger.error("...error.\n")
            
        return

    def load_correct_proxies(self, file_name: Path=cfg.CORRECT_PROXIES_FILE) -> typ.List[AnyUrl]:
        '''
        Reads a proxy list from the file.
        '''
        self._logger.info("Loading correct proxy list...")

        proxy_list = list()
        try:
            with open(self._correct_proxy_filename) as file:
                proxy_list = ''.join(file.readlines()).strip().split("\n")
            self._logger.success("...loaded.\n")
        except:
            self._logger.error("...error.\n")
            
        return proxy_list

    def get_proxy_list(self) -> typ.List[AnyUrl]:
        '''
        Gets a validated list of proxy.
        '''
        proxy_files = self.local_proxy_files
        correct_proxies = list()
        
        self._logger.info("Checking the proxy list...")
        
        for protocol, file_name in proxy_files.items():
            file_path = os.path.join(cfg.PROXY_LISTS_DIR, file_name)
            data = self.check_proxy_list(file_path, protocol)
            data = list(filter(lambda x: x is not None, data))
            
            correct_proxies.extend(data)
            
        self._logger.success("...checked.\n")
        
        _ = self.write_correct_proxies(correct_proxies)
        return correct_proxies

    def prepare_proxy_lists(self, url_general: AnyUrl) -> typ.NoReturn:
        '''
        Prepairs proxy lists for work.
        '''
        self.url_to_check = url_general
        if cfg.DOWNLOAD_PROXY_LISTS:
            _ = self.donload_proxy_lists()
        if cfg.CHECK_PROXIES:
            _ = self.get_proxy_list()

#--Finish functional block