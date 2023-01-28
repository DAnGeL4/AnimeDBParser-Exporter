#--Start imports block
#System imports
import os
import requests
import cfscrape
import typing as typ
from enum import Enum
import dataclasses as dcls
from pydantic import AnyHttpUrl
from flask_session import Session
from pathlib import Path

#Custom imports
from configs.factory import DataclassTypeFactory
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

PROXY_PROTOCOLS = dict({"socks4": "socks4", "socks5": "socks5"})
REQUEST_PROXIES_FORMAT = {
    "http": None,  #used socks proxy
    "https": None  #used socks proxy
}

# Files and Directories

ROOT_DIRECTORY: Path = os.getcwd()
CONFIG_DIR: Path = os.path.join(ROOT_DIRECTORY, "configs/")
MODULES_DIR: Path = os.path.join(ROOT_DIRECTORY, "modules/")
TEMPLATES_DIR: Path = os.path.join(ROOT_DIRECTORY, "templates/")
VARIABLE_DIR: Path = os.path.join(ROOT_DIRECTORY, 'var/')
GLOBAL_LOG_DIR: Path = os.path.join(VARIABLE_DIR, 'logs/')
PROXY_LISTS_DIR: Path = os.path.join(VARIABLE_DIR, "proxy_lists/")
WEB_PAGES_DIR: Path = os.path.join(VARIABLE_DIR, "web_pages/")
JSON_DUMPS_DIR: Path = os.path.join(VARIABLE_DIR, "json_dumps/")
FLASK_SESSION_FILE_DIR: Path = os.path.join(VARIABLE_DIR, "flask_session/")
FLASK_CACHE_DIR: Path = os.path.join(VARIABLE_DIR, "flask_cache/")

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
tp_fc = DataclassTypeFactory()

Response = requests.models.Response
Session = typ.Union[cfscrape.CloudflareScraper, Session]
WebPage = Response
WebPagePart = Response
HTMLTemplate = typ.Union[WebPage, WebPagePart]
JSON = typ.Union[typ.Dict[str, typ.Any], typ.List[typ.Dict[str, typ.Any]]]
Cookies = typ.AnyStr


class RequestMethod(Enum):
    '''Contains types of HTTP requesting methods.'''
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    HEAD = "HEAD"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"


class WatchListType(Enum):
    '''Contains types of watchlists.'''
    WATCH = "watch"
    DESIRED = "desired"
    VIEWED = "viewed"
    ABANDONE = "abandone"
    FAVORITES = "favorites"
    DELAYED = "delayed"
    REVIEWED = "reviewed"


class AnimeType(Enum):
    '''Types of anime.'''
    TV = 'tv-serial'
    OVA = 'ova'
    MOVIE = 'film'
    SPECIAL = 'special'
    ONA = 'ona'
    CLIP = 'clip'


class AnimeStatuse(Enum):
    '''Types of anime statuses.'''
    AIRING = 'airing'
    FINISHED = 'finished'
    UPCOMING = 'upcoming'


class ServerAction(Enum):
    '''Types of server actions.'''
    PARSE = 'parse'
    EXPORT = 'export'


class ActionModule(Enum):
    '''Types of action modules.'''
    PARSER = 'parser'
    EXPORTER = 'exporter'


class AjaxCommand(Enum):
    '''
    Types of commands transmitted 
    from jQuery ajax.
    '''
    START = 'start'
    ASK = 'ask'
    STOP = 'stop'
    DEFAULT = 'default'


class ResponseStatus(Enum):
    '''Types of returned server statuses.'''
    PROCESSED = 'processed'
    DONE = 'done'
    FAIL = 'fail'
    INFO = 'info'
    WARNING = 'warning'
    EMPTY = ''


@dcls.dataclass
class AjaxServerResponse:
    '''
    Server response data type 
    for jQuery ajax.
    '''
    status: ResponseStatus = ResponseStatus.EMPTY
    msg: HTMLTemplate = str()
    title_tmpl: HTMLTemplate = str()
    statusbar_tmpl: HTMLTemplate = str()

    def asdict(self):
        return {
            k: v.value if hasattr(v, 'value') else v
            for k, v in dcls.asdict(self).items()
        }


@dcls.dataclass
class AnimeInfoType:
    '''Anime data type.'''
    poster: AnyHttpUrl
    name: str
    original_name: str
    other_names: typ.List[str]
    type: AnimeType
    ep_count: typ.Union[int, None]
    year: int
    status: AnimeStatuse

    def asdict(self):
        return {k: v for k, v in dcls.asdict(self).items()}


@dcls.dataclass
class LinkedAnimeInfoType(AnimeInfoType):
    '''Anime data type with a link.'''
    link: AnyHttpUrl


TitleDump: typ.Dict = AnimeInfoType
TitleDumpByKey = typ.Dict[str, LinkedAnimeInfoType]
AnimeByWatchList = typ.Dict[WatchListType, TitleDumpByKey]

ProcessedTitlesDump: typ.Union[str, 
    AnimeByWatchList] = tp_fc.build_dataclass_type(
        name='ProcessedTitlesDump',
        fields_types=[TitleDumpByKey] * 8,     #len(fields_container), 
        fields_container=list(WatchListType) + ['errors'], 
        functions=['asdict']
    )

ActionModuleCompatibility = {
    ServerAction.PARSE: ActionModule.PARSER,
    ServerAction.EXPORT: ActionModule.EXPORTER
}

#--Finish global constants block
