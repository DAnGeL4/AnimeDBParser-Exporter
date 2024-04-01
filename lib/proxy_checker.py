#--Start imports block
#System imports
import os
import asyncio
import requests
import multiprocessing as mp
import typing as typ
from pathlib import Path
from functools import partial
from proxybroker2 import Broker
from pydantic import IPvAnyAddress, AnyUrl

#Custom imports
from configs.settings import (LOCAL_PROXY_FILES, ONLINE_PROXY_LISTS,
                              REQUEST_PROXIES_FORMAT, PROXY_LISTS_DIR,
                              CORRECT_PROXIES_FILE, DOWNLOAD_PROXY_LISTS,
                              CHECK_PROXIES, PROXY_CHECK_TIMEOUT,
                              PROXY_PROTOCOLS, PB2_MAX_TRIES,
                              PB2_PROXIES_LIMIT, PB2_FIND_PROXY)
from .tools import OutputLogger

#--Finish imports block


#--Start functional block
class ProxyChecker:
    '''
    The class for download, checking and validate proxy lists.
    '''
    #Constant block
    #----------------------------
    local_proxy_files: Path = LOCAL_PROXY_FILES
    online_proxy_lists: Path = ONLINE_PROXY_LISTS
    proxies: typ.Dict[str, IPvAnyAddress] = REQUEST_PROXIES_FORMAT
    url_to_check: AnyUrl = None
    _module_name: str = None
    _correct_proxy_filename: Path = None

    #----------------------------

    def __init__(self, module_name: str, queue: mp.Queue = None):
        self._module_name = module_name
        self._queue = queue

        filename = f"{self._module_name}_correct_proxies"
        self._correct_proxy_filename = os.path.join(PROXY_LISTS_DIR, filename)

        _redir_out = OutputLogger(duplicate=True,
                                  queue=self._queue,
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
            write_filename = os.path.join(PROXY_LISTS_DIR, file_name)
            open(write_filename, 'wb').write(response.content)

            self._logger.success("...done.")
        self._logger.info("Downloaded.\n")

    def handle(self, proxy: IPvAnyAddress,
               protocol: str) -> typ.Union[AnyUrl, None]:
        '''
        Checks if the proxy address is live 
        and if the request returns a correct response.
        '''
        proxies = self.proxies
        proxies["http"] = proxies["https"] = f"{protocol}://{proxy}"

        try:
            response = requests.get(self.url_to_check,
                                    proxies=proxies,
                                    timeout=PROXY_CHECK_TIMEOUT)
            self._logger.info(f"Live proxy: {protocol}://{proxy}")
            self._logger.info(f"Response: {response}")

            if response.status_code == 200:
                self._logger.success("Valid proxy.\n")
                return f"{protocol}://{proxy}"

        except:
            self._logger.warning(f"Invalid proxy! ({proxy})")

        return

    def check_proxy_list(self, file: Path,
                         protocol: str) -> typ.List[typ.Union[AnyUrl, None]]:
        '''
        Reads the files of the proxy lists 
        and checks the proxies in a multi-flow.
        '''
        data = None

        with open(file) as file:
            proxy_list = ''.join(file.readlines()).strip().split("\n")

        with mp.Pool(mp.cpu_count()) as process:
            data = process.map(partial(self.handle, protocol=protocol),
                               proxy_list)

        return data

    def write_correct_proxies(
            self, correct_proxies: typ.List[AnyUrl]) -> typ.NoReturn:
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

    def load_correct_proxies(self,
                             file_name: Path = CORRECT_PROXIES_FILE
                             ) -> typ.List[AnyUrl]:
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
            file_path = os.path.join(PROXY_LISTS_DIR, file_name)
            data = self.check_proxy_list(file_path, protocol)
            data = list(filter(lambda x: x is not None, data))

            correct_proxies.extend(data)

        self._logger.success("...checked.\n")

        _ = self.write_correct_proxies(correct_proxies)
        return correct_proxies

    def pb2_write_proxies_by_type(
            self, sorted_proxies: typ.Dict[str,
                                           typ.List[str]]) -> typ.NoReturn:
        '''Saves proxies to a file by proxy type.'''
        self._logger.info("Saving proxies in separate files...")
        for proxy_type in sorted_proxies.keys():
            if not proxy_type in self.local_proxy_files:
                continue
            if not sorted_proxies[proxy_type]:
                continue

            filename = self.local_proxy_files[proxy_type]
            full_filename = os.path.join(PROXY_LISTS_DIR, filename)
            self._logger.info(f"...saving {proxy_type} proxies...")
            try:
                with open(full_filename, 'a') as file:
                    file.writelines(sorted_proxies[proxy_type])
                self._logger.info("...done...")
            except:
                self._logger.error("...error...")
        self._logger.info("...Saving finished...")

    async def pb2_get_proxies(self,
                              proxies: asyncio.Queue) -> typ.Dict[str, list]:
        '''Gets proxies from proxybroker2.'''
        self._logger.info("Getting proxies...")
        sorted_proxies = {"http": [], "https": [], "socks4": [], "socks5": []}

        count = 0
        total_count = PB2_PROXIES_LIMIT
        step = round(PB2_PROXIES_LIMIT / 100)
        step = 1 if step < 1 else step
        next_step = step

        while True:
            proxy = await proxies.get()
            if proxy is None: break

            count += 1
            if count % next_step == 0:
                self._logger.info(f"...{count} of {total_count} received...")

            for proxy_type in proxy.types.keys():
                proxy_type = proxy_type.lower()
                row = '%s:%s\n' % (proxy.host, proxy.port)
                sorted_proxies[proxy_type].append(row)
                print(row)

        self._logger.info("...Done.\n")
        return sorted_proxies

    async def pb2_get_n_save_by_type(self,
                                     proxies: asyncio.Queue) -> typ.NoReturn:
        '''Gets and saves proxies to a file.'''
        sorted_proxies = await self.pb2_get_proxies(proxies)
        _ = self.pb2_write_proxies_by_type(sorted_proxies)

    def pb2_find_proxy(self) -> typ.NoReturn:
        '''Finds and saves proxies to a file.'''
        self._logger.info("Proxy search started (using ProxyBroker2)...")
        proxies = asyncio.Queue()
        broker = Broker(proxies,
                        timeout=PROXY_CHECK_TIMEOUT,
                        max_tries=PB2_MAX_TRIES)
        proxy_types = list(map(str.upper, PROXY_PROTOCOLS.values()))
        # HTTPS proxy search does not work correctly in ProxyBroker2
        # so remove it from the list
        if 'HTTPS' in proxy_types: proxy_types.remove('HTTPS')
        self._logger.info(f"...searched types:{proxy_types}...\n")

        tasks = asyncio.gather(
            broker.find(types=proxy_types, post=True, limit=PB2_PROXIES_LIMIT),
            self.pb2_get_n_save_by_type(proxies))

        loop = asyncio.get_event_loop()
        _ = loop.run_until_complete(tasks)
        self._logger.info("Proxy search ended (using ProxyBroker2).\n")

    def prepare_proxy_lists(self) -> typ.NoReturn:
        '''Prepares proxy lists for work.'''
        if DOWNLOAD_PROXY_LISTS:
            _ = self.donload_proxy_lists()
        if PB2_FIND_PROXY:
            _ = self.pb2_find_proxy()

    def check_proxy_lists_by_modules(self,
                                     url_general: AnyUrl) -> typ.NoReturn:
        '''
        Checks the proxy lists by modules.
        '''
        self.url_to_check = url_general
        if CHECK_PROXIES:
            _ = self.get_proxy_list()

#--Finish functional block