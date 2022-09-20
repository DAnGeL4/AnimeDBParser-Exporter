#--Start imports block
#System imports
import os
import requests
import cfscrape
from enum import Enum
import typing as typ
from pydantic import AnyHttpUrl
#--Finish imports block


#--Start global constants block
DOWNLOAD_PROXY_LISTS = bool(    False
                                #True
)
CHECK_PROXIES = bool(           False
                                #True
)
WRITE_LOG_TO_FILE = bool(       #False
                                True
)
RELOAD_WEB_PAGES = bool(        False
                                #True
)
UPDATE_JSON_DUMPS = bool(       False
                                #True
)
USE_MULTITHREADS = bool(        #False
                                True
)

PROXY_PROTOCOLS = dict({
    "socks4": "socks4",
    "socks5": "socks5"
})
REQUEST_PROXIES_FORMAT = {
    "http": None,            #used socks proxy
    "https": None            #used socks proxy
}

ROOT_DIRECTORY = os.getcwd()
CONFIG_DIR = os.path.join(ROOT_DIRECTORY, "configs/")
MODULES_DIR = os.path.join(ROOT_DIRECTORY, "modules/")
VARIABLE_DIR = os.path.join(ROOT_DIRECTORY, 'var/')
GLOBAL_LOG_DIR = os.path.join(VARIABLE_DIR, 'logs/')
PROXY_LISTS_DIR = os.path.join(VARIABLE_DIR, "proxy_lists/")
WEB_PAGES_DIR = os.path.join(VARIABLE_DIR, "web_pages/")
JSON_DUMPS_DIR = os.path.join(VARIABLE_DIR, "json_dumps/")

CORRECT_PROXIES_FILE = os.path.join(PROXY_LISTS_DIR, "correct_proxies")
GLOBAL_LOG_FILE = os.path.join(GLOBAL_LOG_DIR, 'general_log.log')
LOCAL_PROXY_FILES = dict({
    PROXY_PROTOCOLS["socks4"]: "proxy_socks4",
    PROXY_PROTOCOLS["socks5"]: "proxy_socks5",
})
ONLINE_PROXY_LISTS = dict({
    LOCAL_PROXY_FILES[PROXY_PROTOCOLS["socks4"]]: 
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
    LOCAL_PROXY_FILES[PROXY_PROTOCOLS["socks5"]]: 
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
})

#Types
Response = requests.models.Response
Session = cfscrape.CloudflareScraper
WebPage = Response    

class WatchListTypes(Enum):
    WATCH = "watch"
    DESIRED = "desired"
    VIEWED = "viewed"
    ABANDONE = "abandone"
    FAVORITES = "favorites"

class AnimeInfoType(typ.NamedTuple):
    '''
    Anime data type.
    '''
    poster: AnyHttpUrl
    name: str
    original_name: str
    other_names: typ.List[str]
    type: typ.Union[ 
        typ.Literal['tv-serial'],
        typ.Literal['ova'],
        typ.Literal['film'],
        typ.Literal['special'],
        typ.Literal['ona'],
        typ.Literal['clip']
    ]
    ep_count: typ.Union[int, None]
    year: int
    status: typ.Union[ 
        typ.Literal['airing'],
        typ.Literal['finished'],
        typ.Literal['upcoming']
    ]

#--Finish global constants block