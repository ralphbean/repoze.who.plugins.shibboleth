"""TurboGears middleware initialization"""
from repoze.who.config import make_middleware_with_config as make_who_with_config

from ldapauth.config.app_cfg import base_config
from ldapauth.config.environment import load_environment

#Use base_config to setup the nessisary WSGI App factory. 
#make_base_app will wrap the TG2 app with all the middleware it needs. 
make_base_app = base_config.setup_tg_wsgi_app(load_environment)

def make_app(global_conf, full_stack=True, **app_conf):
    app = make_base_app(global_conf, full_stack=True, **app_conf)
    #Wrap your base turbogears app with custom middleware
    app = make_who_with_config(app, global_conf, app_conf['who.config_file'], 
                               app_conf['who.log_file'], 
                               app_conf['who.log_level'])
    return app


