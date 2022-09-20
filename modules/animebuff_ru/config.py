#--Start imports block
#System imports
import os
#Custom imports
from configs import settings as cfg
from configs import abstract_classes as ac
#--Finish imports block


#--Start global constants block
class AnimeBuffRuConfig(ac.SiteSettings):
    '''Configuration for site animebuff.ru.'''

    _user_num = os.environ['animebuff_user_num']
    _login = os.environ['animebuff_login']
    _password = os.environ['animebuff_pwd']
    payload = {'username': _login, 'password': _password}

    use_proxy = True
    proxies = cfg.REQUEST_PROXIES_FORMAT
    
    url_domain = "animebuff.ru"
    url_general = "https://animebuff.ru"
    url_login = "https://animebuff.ru/login"
    url_wath_lists = f"https://animebuff.ru/users/{_user_num}/watchlist"
    url_type_option = "?type="
    
    url_types = {
        cfg.WatchListTypes.WATCH: 
            "%D0%A1%D0%BC%D0%BE%D1%82%D1%80%D1%8E",
        cfg.WatchListTypes.DESIRED: 
            "%D0%91%D1%83%D0%B4%D1%83%20%D1%81%D0%BC%D0%BE%D1%82%D1%80%D0%B5%D1%82%D1%8C",
        cfg.WatchListTypes.VIEWED: 
            "%D0%9F%D1%80%D0%BE%D1%81%D0%BC%D0%BE%D1%82%D1%80%D0%B5%D0%BD%D0%BE",
        cfg.WatchListTypes.ABANDONE: 
            "%D0%97%D0%B0%D0%B1%D1%80%D0%BE%D1%88%D0%B5%D0%BD%D0%BE",
        cfg.WatchListTypes.FAVORITES: 
            "%D0%98%D0%B7%D0%B1%D1%80%D0%B0%D0%BD%D0%BD%D0%BE%D0%B5"
    }
    
    cookies = {
        "animebuff_session": os.environ['animebuff_session_value'],
        "XSRF-TOKEN": os.environ['XSRF-TOKEN-VALUE']
    }
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        #"Accept-Encoding": "gzip, deflate, br",
        #"Accept-Language": "ru,en-US;q=0.8,en;q=0.5,be;q=0.3",
        #"Alt-Used": "animebuff.ru",
        #"Cache-Control": "max-age=0",
        #"Connection": "keep-alive",
        #"Cookie": "XSRF-TOKEN=" + os.environ['XSRF-TOKEN-VALUE'] + 
        #            "; animebuff_session="+ os.environ['animebuff_session_value'],
        #"DNT": "1",
        #"Host": "animebuff.ru",
        #"Referer": "https://animebuff.ru/users/4718",
        #"Sec-Fetch-Dest": "document",
        #"Sec-Fetch-Mode": "navigate",
        #"Sec-Fetch-Site": "same-origin",
        ##"Sec-Fetch-Site": "none",
        #"Sec-Fetch-User": "?1",
        #"Upgrade-Insecure-Requests": "1",
        "User-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0"
    }
#--Finish global constants block