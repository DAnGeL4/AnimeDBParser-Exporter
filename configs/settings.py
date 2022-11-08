#--Start imports block
#System imports
import os
import requests
import cfscrape
import typing as typ
from enum import Enum
from dataclasses import dataclass
from pydantic import AnyHttpUrl
from dataclasses import asdict
#--Finish imports block


#--Start global constants block

# Flags

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
ENABLE_PARSING_MODULES = bool(  #False
                                True
)
ENABLE_EXPORTER_MODULES = bool( #False
                                True
)

# Web Protocols

PROXY_PROTOCOLS = dict({
    "socks4": "socks4",
    "socks5": "socks5"
})
REQUEST_PROXIES_FORMAT = {
    "http": None,            #used socks proxy
    "https": None            #used socks proxy
}

# Files and Directories

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

# Online Files

ONLINE_PROXY_LISTS = dict({
    LOCAL_PROXY_FILES[PROXY_PROTOCOLS["socks4"]]: 
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
    LOCAL_PROXY_FILES[PROXY_PROTOCOLS["socks5"]]: 
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
})

# Types

Response = requests.models.Response
Session = cfscrape.CloudflareScraper
WebPage = Response    
JSON = typ.Union[typ.Dict[str, typ.Any], typ.List[typ.Dict[str, typ.Any]]]
Cookies = typ.AnyStr

class RequestMethods(Enum):
    '''Contains types of HTTP requesting methods.'''
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    HEAD = "HEAD"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"


class WatchListTypes(Enum):
    '''Contains types of watchlists.'''
    WATCH = "watch"
    DESIRED = "desired"
    VIEWED = "viewed"
    ABANDONE = "abandone"
    FAVORITES = "favorites"
    DELAYED = "delayed"
    REVIEWED = "reviewed"

class AnimeTypes(Enum):
    '''Types of anime.'''
    TV = 'tv-serial'
    OVA = 'ova'
    MOVIE = 'film'
    SPECIAL = 'special'
    ONA = 'ona'
    CLIP = 'clip'


class AnimeStatuses(Enum):
    '''Types of anime statuses.'''
    AIRING = 'airing'
    FINISHED = 'finished'
    UPCOMING = 'upcoming'

    
@dataclass
class AnimeInfoType:
    '''Anime data type.'''
    poster: AnyHttpUrl
    name: str
    original_name: str
    other_names: typ.List[str]
    type: AnimeTypes
    ep_count: typ.Union[int, None]
    year: int
    status: AnimeStatuses

    def _asdict(self):
        return {k: v for k, v in asdict(self).items()}

@dataclass
class LinkedAnimeInfoType(AnimeInfoType):
    '''Anime data type with a link.'''
    link: AnyHttpUrl


TitleDump: typ.Dict = AnimeInfoType
TitleDumpByKey = typ.Dict[str, TitleDump]
AnimeByWatchList = typ.Dict[WatchListTypes, TitleDumpByKey]

WatchListCompatibility = dict({
    'watch': WatchListTypes.WATCH,
    'desired': WatchListTypes.DESIRED,
    'viewed': WatchListTypes.VIEWED,
    'abandone': WatchListTypes.ABANDONE,
    'favorites': WatchListTypes.FAVORITES,
    'delayed': WatchListTypes.DELAYED,
    'reviewed': WatchListTypes.REVIEWED
})

#--Finish global constants block