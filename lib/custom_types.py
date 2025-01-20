#--Start imports block
#System imports
from enum import Enum
import typing as typ
import dataclasses as dcls
from pydantic import AnyHttpUrl

import requests
from cfscrape import CloudflareScraper
from flask_session import Session as FlaskSession
from celery import Task as CeleryTask

#Custom imports
from configs.settings import TITLES_DUMP_KEY_ERRORS
from .factory import DataclassTypeFactory
#--Finish imports block

#--Start global constants block
tp_fc = DataclassTypeFactory()

Response = requests.models.Response
Session = typ.Union[CloudflareScraper, FlaskSession]
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


class EnabledDataHandler(Enum):
    '''Contains types of data handlers.'''
    JSON = "json"
    CACHE = "cache"
    REDIS = "redis"
    
class EnabledProgressHandler(Enum):
    '''Contains types of data handlers.'''
    CACHE = "cache"


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


class AnimeStatus(Enum):
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
    status: ResponseStatus
    msg: HTMLTemplate
    title_tmpl: HTMLTemplate
    statusbar_tmpl: HTMLTemplate

    def __post_init__(self):
        self.status = ResponseStatus.EMPTY
        self.msg = str()
        self.title_tmpl = str()
        self.statusbar_tmpl = str()

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
    status: AnimeStatus

    def asdict(self):
        return {
            k: v.value if hasattr(v, 'value') else v
            for k, v in dcls.asdict(self).items()
        }

    @classmethod
    def fields_count(cls):
        # len(dcls.fields(AnimeInfoType))
        return 9


@dcls.dataclass
class LinkedAnimeInfoType(AnimeInfoType):
    '''Anime data type with a link.'''
    link: AnyHttpUrl


TitleDump: typ.Dict = AnimeInfoType
TitleDumpByKey = typ.Dict[str, LinkedAnimeInfoType]
AnimeByWatchList = typ.Dict[WatchListType, TitleDumpByKey]

DEFAULT_DATA_HANDLER = EnabledDataHandler.JSON
DEFAULT_PROGRESS_HANDLER = EnabledProgressHandler.CACHE

__fields_container = list(WatchListType) + [TITLES_DUMP_KEY_ERRORS]
ProcessedTitlesDump: typ.Union[str,
                               AnimeByWatchList] = tp_fc.build_dataclass_type(
   name='ProcessedTitlesDump',
   fields_types=[TitleDumpByKey] * len(__fields_container),
   fields_container=__fields_container,
   functions=['asdict']
)
del __fields_container


@dcls.dataclass
class ITitlesProgressStatusCommon:
    '''
    Stores the state of the titles processing progress.
    '''
    now: int 
    max: int 
    
    def __post_init__(self):
        self.now = 0
        self.max = 0
    
@dcls.dataclass
class TitlesProgressStatusAll(ITitlesProgressStatusCommon):
    '''
    Stores the state of the overall progress 
    of processing titles.
    '''
    pass


@dcls.dataclass
class TitlesProgressStatusCurrent(ITitlesProgressStatusCommon):
    '''
    Stores the progress status of titles 
    for the current watchlist.
    '''
    watchlist: WatchListType

    def __post_init__(self):
        self.watchlist = ''

@dcls.dataclass
class TitlesProgressStatus:
    '''
    Container-type to store the progress state 
    of a running server action.
    '''
    status: bool
    all: TitlesProgressStatusAll
    current: TitlesProgressStatusCurrent
    
    def __post_init__(self):
        self.status = False
        self.all = TitlesProgressStatusAll()
        self.current = TitlesProgressStatusCurrent()
    
    def asdict(self):
        return {k: v for k, v in dcls.asdict(self).items()}
#---

# Compatibility tables
#---
ActionToModuleCompatibility: typ.Dict[ServerAction, ActionModule] = {
    ServerAction.PARSE: ActionModule.PARSER,
    ServerAction.EXPORT: ActionModule.EXPORTER
}
#---

#--Finish global constants block
