#--Start imports block
#System imports
import os
import requests
import cfscrape
import typing as typ
from enum import Enum
import dataclasses as dcls
from pydantic import AnyHttpUrl, Protocol, HttpUrl
from flask_session import Session
from datetime import timedelta
from pathlib import Path
from celery import Task as CeleryTask

#Custom imports
from lib.factory import DataclassTypeFactory
#--Finish imports block

#--Start global constants block

# Flags
#---
DOWNLOAD_PROXY_LISTS: bool = bool(
    False
    #True
)
CHECK_PROXIES: bool = bool(
    False
    #True
)
WRITE_LOG_TO_FILE: bool = bool(
    #False
    True
)
RELOAD_WEB_PAGES: bool = bool(
    False
    #True
)
UPDATE_JSON_DUMPS: bool = bool(
    #False
    True
)
USE_MULTITHREADS: bool = bool(  
    #False
    True
)
ENABLE_PARSING_MODULES: bool = bool(
    #False
    True
)
ENABLE_EXPORTER_MODULES: bool = bool(
    #False
    True
)
RESTART_CELERY_WORKERS: bool = bool(
    False
    #True
)
CELERY_USE_PICKLE_SERIALIZER = bool(
    True
    #False
)
USE_DATABASE = bool(
    #True
    False
)
#---

# Common constants
#---
CELERY_TASKS_MODULE = 'modules.flask.celery_tasks'
FLASK_APPLICATION_NAME: str = "CIE"
FLASK_SESSION_FILE_THRESHOLD = 10
FLASK_TIME_TO_LIVE = int(timedelta(hours=2).total_seconds())
FLASK_SESSION_TIME_TO_LIVE = FLASK_TIME_TO_LIVE
FLASK_CACHE_TIME_TO_LIVE = FLASK_TIME_TO_LIVE
FLASK_SESSION_TYPE = 'filesystem'
FLASK_CACHE_TYPE = 'filesystem'
#---

# Web Protocols
#---
PROXY_PROTOCOLS: typ.Dict[str, Protocol] = dict({
    "socks4": "socks4",
    "socks5": "socks5"
})
REQUEST_PROXIES_FORMAT: typ.Dict[Protocol, AnyHttpUrl] = {
    "http": None,  #used socks proxy
    "https": None  #used socks proxy
}
#---

# URLs
#---
CELERY_BROKER_URL: AnyHttpUrl = 'redis://localhost:6379'
CELERY_RESULT_BACKEND: AnyHttpUrl = 'redis://localhost:6379'
#---

# Files and Directories
#---
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
SH_DIR: Path = os.path.join(ROOT_DIRECTORY, "sh_scripts/")

REDIS_SETUP_SH_FILE: Path = os.path.join(SH_DIR, "redis_up.sh")
CELERY_SETUP_SH_FILE: Path = os.path.join(SH_DIR, "celery_worker_up.sh")
CORRECT_PROXIES_FILE: Path = os.path.join(PROXY_LISTS_DIR, "correct_proxies")
GLOBAL_LOG_FILE: Path = os.path.join(GLOBAL_LOG_DIR, 'general_log.log')
COMMON_BASH_LOG_FILE: Path = os.path.join(GLOBAL_LOG_DIR, "bash.log")
LOCAL_PROXY_FILES: typ.Dict[Protocol, str] = dict({
    PROXY_PROTOCOLS["socks4"]: "proxy_socks4",
    PROXY_PROTOCOLS["socks5"]: "proxy_socks5",
})
#---

# Online Files
#---
ONLINE_PROXY_LISTS: typ.Dict[str, HttpUrl] = dict({
    LOCAL_PROXY_FILES[PROXY_PROTOCOLS["socks4"]]:
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
    LOCAL_PROXY_FILES[PROXY_PROTOCOLS["socks5"]]:
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
})
#---

# Types
#---
tp_fc = DataclassTypeFactory()

Response = requests.models.Response
Session = typ.Union[cfscrape.CloudflareScraper, Session]
WebPage = Response
WebPagePart = Response
HTMLTemplate = typ.Union[WebPage, WebPagePart]
JSON = typ.Union[typ.Dict[str, typ.Any], typ.List[typ.Dict[str, typ.Any]]]
Cookies = typ.AnyStr
CeleryTaskID: CeleryTask = str


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
    genres: typ.List[str]
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
                                   fields_types=[TitleDumpByKey] *
                                   8,  #len(fields_container), 
                                   fields_container=list(WatchListType) +
                                   ['errors'],
                                   functions=['asdict'])
#---

# Compatibility tables
#---
ActionToModuleCompatibility: typ.Dict[ServerAction, ActionModule] = {
    ServerAction.PARSE: ActionModule.PARSER,
    ServerAction.EXPORT: ActionModule.EXPORTER
}
#---

#--Finish global constants block
