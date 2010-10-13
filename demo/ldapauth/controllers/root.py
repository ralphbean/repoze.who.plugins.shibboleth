"""Main Controller"""

from tg import expose, flash
from pylons import request
from paste.httpexceptions import HTTPUnauthorized

from ldapauth.lib.base import BaseController


class RootController(BaseController):
    @expose('ldapauth.templates.index')
    def index(self):
        return dict()

    @expose('ldapauth.templates.about')
    def about(self):
        if request.environ.get('repoze.who.identity') == None:
            raise HTTPUnauthorized()
        user = request.environ['repoze.who.identity']['repoze.who.userid']
        flash('Your Distinguished Name (DN) is "%s"' % user)
        # Passing the metadata
        metadata = request.environ['repoze.who.identity']
        return dict(metadata=metadata.items())
