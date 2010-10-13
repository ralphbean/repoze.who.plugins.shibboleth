"""Setup the LDAPAuth application"""
import logging

import transaction
from paste.deploy import appconfig
from tg import config

from ldapauth.config.environment import load_environment

log = logging.getLogger(__name__)

def setup_config(command, filename, section, vars):
    """Place any commands to setup ldapauth here"""
    conf = appconfig('config:' + filename)
    load_environment(conf.global_conf, conf.local_conf)
    # Load the models
    #from ldapauth import model
    #print "Creating tables"
    #model.metadata.create_all(bind=config['pylons.app_globals'].sa_engine)

    print """
================= Demo Project for repoze.who.plugins.ldap ====================

You should setup this demo by creating the relevant users and groups in your
LDAP server, and then adjusting the relevant parameters in the "who.ini" file.

"""
    
    #transaction.commit()
    
    print "Successfully setup"
