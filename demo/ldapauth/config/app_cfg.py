from tg.configuration import AppConfig, Bunch
import ldapauth
from ldapauth import model
from ldapauth.lib import app_globals, helpers

base_config = AppConfig()
base_config.renderers = []

base_config.package = ldapauth

#Set the default renderer
base_config.default_renderer = 'genshi'
base_config.renderers.append('genshi') 

#Configure the base SQLALchemy Setup
base_config.use_sqlalchemy = True
base_config.model = ldapauth.model
base_config.DBSession = ldapauth.model.DBSession

