#--Start imports block
#Custom imports
from configs import abstract_classes as ac
from modules.animebuff_ru.config import AnimeBuffRuConfig
from modules.animebuff_ru.web_page_tools import WebPageParser as AnimeBuffRuParser
#--Finish imports block


#--Start functional block
class ModuleAnimeBuffRu(ac.ConnectedParserModuleType):
    '''Contains the submodules for the animebuff.ru site.'''
    module_name = "animebuff_ru"
    json_dump_name = module_name + ".json"
    config_module = AnimeBuffRuConfig
    parser_module = AnimeBuffRuParser
    
class ModuleAnimeGoOrg(ac.ConnectedSubmitModuleType):
    '''Contains the submodules for the animebuff.ru site.'''
    module_name = "animego_org"
    #json_dump_name = "animebuff_ru.json"
    config_module = None
    #parser_module = AnimeBuffRuParser
    submit_module = None


EnabledParserModules = list([
    ModuleAnimeBuffRu,
])

EnabledSubmitModules = list([
    #ModuleAnimeGoOrg,
])
#--Finish functional block