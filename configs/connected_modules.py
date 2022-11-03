#--Start imports block
#System imports
from enum import Enum

#Custom imports
from configs import abstract_classes as ac

from modules.animebuff_ru.config import AnimeBuffRuConfig
from modules.animebuff_ru.web_page_tools import WebPageParser as AnimeBuffRuParser

from modules.animego_org.config import AnimeGoOrgConfig
from modules.animego_org.web_page_tools import WebPageParser as AnimeGoOrgParser
#--Finish imports block


#--Start functional block
class ModuleAnimeBuffRu(ac.ConnectedModuleType):
    '''Contains the submodules for the animebuff.ru site.'''
    module_name = "animebuff_ru"
    json_dump_name = module_name + ".json"
    config_module = AnimeBuffRuConfig
    parser_module = AnimeBuffRuParser
    
class ModuleAnimeGoOrg(ac.ConnectedModuleType):
    '''Contains the submodules for the animego.org site.'''
    module_name = "animego_org"
    json_dump_name = module_name + ".json"
    config_module = AnimeGoOrgConfig
    parser_module = AnimeGoOrgParser


EnabledParserModules = list([
    ModuleAnimeBuffRu,
])

EnabledSubmitModules = list([
    ModuleAnimeGoOrg,
])


class EnabledModules(Enum):
    '''Contains lists of modules by actions.'''
    parse = EnabledParserModules
    export = EnabledSubmitModules
#--Finish functional block