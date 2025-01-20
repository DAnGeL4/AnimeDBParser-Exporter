#--Start imports block
#System imports
from enum import Enum

#Custom imports
from lib.custom_types import ServerAction
from lib.interfaces import IConnectedModule

from modules.animebuff_ru.config import AnimeBuffRuConfig
from modules.animebuff_ru.web_page_tools import WebPageParser as AnimeBuffRuParser

from modules.animego_org.config import AnimeGoOrgConfig
from modules.animego_org.web_page_tools import WebPageParser as AnimeGoOrgParser

#--Finish imports block


#--Start global constants block
class ModuleAnimeBuffRu(IConnectedModule):
    '''Contains the submodules for the animebuff.ru site.'''
    presented_name = "AnimeBuff.Ru"
    module_name = "animebuff_ru"
    json_dump_name = module_name + ".json"
    config_module = AnimeBuffRuConfig
    parser_module = AnimeBuffRuParser


class ModuleAnimeGoOrg(IConnectedModule):
    '''Contains the submodules for the animego.org site.'''
    presented_name = "AnimeGo.Org"
    module_name = "animego_org"
    json_dump_name = module_name + ".json"
    config_module = AnimeGoOrgConfig
    parser_module = AnimeGoOrgParser


EnabledParserModules = list([
    ModuleAnimeBuffRu,
])

EnabledExporterModules = list([
    ModuleAnimeGoOrg,
])

EnabledModules = Enum(
    'EnabledModules', {
        ServerAction.PARSE.value: EnabledParserModules,
        ServerAction.EXPORT.value: EnabledExporterModules
    })
EnabledModules.__doc__ = "Contains lists of modules by actions."

NameToModuleCompatibility = Enum(
    'NameToModuleCompatibility', {
        mod.presented_name: mod 
        for mod in [*EnabledParserModules, *EnabledExporterModules]
    })
NameToModuleCompatibility.__doc__ = \
        "Contains lists of modules by presented names."

#--Finish global constants block
