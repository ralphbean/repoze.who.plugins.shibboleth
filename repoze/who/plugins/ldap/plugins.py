# -*- coding: utf-8 -*-
#
# repoze.who.plugins.ldap, LDAP authentication for WSGI applications.
# Copyright (C) 2010 by Gustavo Narea  <http://gustavonarea.net/> and
#                       Lorenzo M. Catucci <http://www.uniroma2.it/>.
# Copyright (C) 2008 by Gustavo Narea <http://gustavonarea.net/>.
#
# This file is part of repoze.who.plugins.ldap
# <http://code.gustavonarea.net/repoze.who.plugins.ldap/>
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE.
"""LDAP plugins for repoze.who."""

__all__ = ['LDAPBaseAuthenticatorPlugin', 'LDAPAuthenticatorPlugin',
           'LDAPSearchAuthenticatorPlugin', 'LDAPAttributesPlugin']

from zope.interface import implements
import ldap

from repoze.who.interfaces import IAuthenticator, IMetadataProvider

from base64 import b64encode, b64decode

import re


#{ Authenticators


class LDAPBaseAuthenticatorPlugin(object):

    implements(IAuthenticator)

    def __init__(self, ldap_connection, base_dn, returned_id='dn',
                 start_tls=False, bind_dn='', bind_pass='', **kwargs):
        """Create an LDAP authentication plugin.
        
        By passing an existing LDAPObject, you're free to use the LDAP
        authentication method you want, the way you want.
   
        This is an *abstract* class, which means it's useless in itself. You
        can only use subclasses of this class that implement the L{_get_dn}
        method (e.g., the built-in authenticators).
        
        This plugin is compatible with any identifier plugin that defines the
        C{login} and C{password} items in the I{identity} dictionary.
        
        @param ldap_connection: An initialized LDAP connection.
        @type ldap_connection: C{ldap.ldapobject.SimpleLDAPObject}

        @param base_dn: The base for the I{Distinguished Name}. Something like
            C{ou=employees,dc=example,dc=org}, to which will be prepended the
            user id: C{uid=jsmith,ou=employees,dc=example,dc=org}.
        @type base_dn: C{unicode}
        @param returned_id: Should we return the full DN or just the
            bare naming identifier value on successful authentication?
        @type returned_id: C{str}, 'dn' or 'login'
        @attention: While the DN is always unique, if you configure the
            authenticator plugin to return the bare naming attribute,
            you have to ensure its uniqueness in the DIT.
        @param start_tls: Should we negotiate a TLS upgrade on the connection with
            the directory server?
        @type start_tls: C{bool}
        @param bind_dn: Operate as the bind_dn directory entry
        @type bind_dn: C{str}
        @param bind_pass: The password for bind_dn directory entry
        @type bind_pass: C{str}
        @raise ValueError: If at least one of the parameters is not defined.
        
        """
        if base_dn is None:
            raise ValueError('A base Distinguished Name must be specified')
        self.ldap_connection = make_ldap_connection(ldap_connection)

        if start_tls:
            try:
                self.ldap_connection.start_tls_s()
            except:
                raise ValueError('Cannot upgrade the connection')

        self.bind_dn = bind_dn
        self.bind_pass = bind_pass

        self.base_dn = base_dn

        if returned_id.lower() == 'dn':
            self.ret_style = 'd'
        elif returned_id.lower() == 'login':
            self.ret_style = 'l'
        else:
            raise ValueError("The return style should be 'dn' or 'login'")

    def _get_dn(self, environ, identity):
        """
        Return the user DN based on the environment and the identity.

        Must be implemented in a subclass
        
        @param environ: The WSGI environment.
        @param identity: The identity dictionary.
        @return: The Distinguished Name (DN)
        @rtype: C{unicode}
        @raise ValueError: If the C{login} key is not in the I{identity} dict.
        
        """
        raise ValueError('Unimplemented')


    # IAuthenticatorPlugin
    def authenticate(self, environ, identity):
        """Return the naming identifier of the user to be authenticated.
        
        @return: The naming identifier, if the credentials were valid.
        @rtype: C{unicode} or C{None}
        
        """
        
        try:
            dn = self._get_dn(environ, identity)
            password = identity['password']
        except (KeyError, TypeError, ValueError):
            return None

        if not hasattr(self.ldap_connection, 'simple_bind_s'):
            environ['repoze.who.logger'].warn('Cannot bind with the provided '
                                              'LDAP connection object')
            return None
        
        try:
            self.ldap_connection.simple_bind_s(dn, password)
            userdata = identity.get('userdata', '')
            # The credentials are valid!
            if self.ret_style == 'd':
                return dn
            else:
                identity['userdata'] = userdata + '<dn:%s>' % b64encode(dn)
                return identity['login']
        except ldap.LDAPError:
            return None

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, id(self))


class LDAPAuthenticatorPlugin(LDAPBaseAuthenticatorPlugin):

    def __init__(self, ldap_connection, base_dn, naming_attribute='uid',
                 **kwargs):
        """Create an LDAP authentication plugin using pattern-determined DNs
        
        By passing an existing LDAPObject, you're free to use the LDAP
        authentication method you want, the way you want.
    
        This plugin is compatible with any identifier plugin that defines the
        C{login} and C{password} items in the I{identity} dictionary.
        
        @param ldap_connection: An initialized LDAP connection.
        @type ldap_connection: C{ldap.ldapobject.SimpleLDAPObject}
        @param base_dn: The base for the I{Distinguished Name}. Something like
            C{ou=employees,dc=example,dc=org}, to which will be prepended the
            user id: C{uid=jsmith,ou=employees,dc=example,dc=org}.
        @type base_dn: C{unicode}
        @param naming_attribute: The naming attribute for directory entries,
            C{uid} by default.
        @type naming_attribute: C{unicode}

        @raise ValueError: If at least one of the parameters is not defined.

        The following parameters are inherited from 
        L{LDAPBaseAuthenticatorPlugin.__init__}
        @param base_dn: The base for the I{Distinguished Name}. Something like
            C{ou=employees,dc=example,dc=org}, to which will be prepended the
            user id: C{uid=jsmith,ou=employees,dc=example,dc=org}.
        @param returned_id: Should we return full Directory Names or just the
            bare naming identifier on successful authentication?
        @param start_tls: Should we negotiate a TLS upgrade on the connection with
            the directory server?
        @param bind_dn: Operate as the bind_dn directory entry
        @param bind_pass: The password for bind_dn directory entry
        

        """
        LDAPBaseAuthenticatorPlugin.__init__(self, ldap_connection, base_dn,
                                             **kwargs)
        self.naming_pattern = u'%s=%%s,%%s' % naming_attribute

    def _get_dn(self, environ, identity):
        """
        Return the user naming identifier based on the environment and the
        identity.
        
        If the C{login} item of the identity is C{rms} and the base DN is
        C{ou=developers,dc=gnu,dc=org}, the resulting DN will be:
        C{uid=rms,ou=developers,dc=gnu,dc=org}
        
        @param environ: The WSGI environment.
        @param identity: The identity dictionary.
        @return: The Distinguished Name (DN)
        @rtype: C{unicode}
        @raise ValueError: If the C{login} key is not in the I{identity} dict.
        
        """

        if self.bind_dn:
            try:
                self.ldap_connection.bind_s(self.bind_dn, self.bind_password)
            except ldap.LDAPError:
                raise ValueError("Couldn't bind with supplied credentials")
        try:
            return self.naming_pattern % ( identity['login'], self.base_dn)
        except (KeyError, TypeError):
            raise ValueError


class LDAPSearchAuthenticatorPlugin(LDAPBaseAuthenticatorPlugin):

    def __init__(self, ldap_connection, base_dn, naming_attribute='uid',
                 search_scope='subtree', restrict='', **kwargs):
        """Create an LDAP authentication plugin determining the DN via LDAP searches.
        
        By passing an existing LDAPObject, you're free to use the LDAP
        authentication method you want, the way you want.
    
        This plugin is compatible with any identifier plugin that defines the
        C{login} and C{password} items in the I{identity} dictionary.
        
        @param ldap_connection: An initialized LDAP connection.
        @type ldap_connection: C{ldap.ldapobject.SimpleLDAPObject}
        @param base_dn: The base for the I{Distinguished Name}. Something like
            C{ou=employees,dc=example,dc=org}, to which will be prepended the
            user id: C{uid=jsmith,ou=employees,dc=example,dc=org}.
        @type base_dn: C{unicode}
        @param naming_attribute: The naming attribute for directory entries,
            C{uid} by default.
        @type naming_attribute: C{unicode}
        @param search_scope: Scope for ldap searches
        @type search_scope: C{str}, 'subtree' or 'onelevel', possibly
            abbreviated to at least the first three characters
        @param restrict: An ldap filter which will be ANDed to the search filter
            while searching for entries matching the naming attribute
        @type restrict: C{unicode}
        @attention: restrict will be interpolated into the search string as a
            bare string like in "(&%s(identifier=login))". It must be correctly
            parenthesised for such usage as in restrict = "(objectClass=*)". 

        @raise ValueError: If at least one of the parameters is not defined.

        The following parameters are inherited from 
        L{LDAPBaseAuthenticatorPlugin.__init__}
        @param base_dn: The base for the I{Distinguished Name}. Something like
            C{ou=employees,dc=example,dc=org}, to which will be prepended the
            user id: C{uid=jsmith,ou=employees,dc=example,dc=org}.
        @param returned_id: Should we return full Directory Names or just the
            bare naming identifier on successful authentication?
        @param start_tls: Should we negotiate a TLS upgrade on the connection
            with the directory server?
        @param bind_dn: Operate as the bind_dn directory entry
        @param bind_pass: The password for bind_dn directory entry
        
        """
        LDAPBaseAuthenticatorPlugin.__init__(self, ldap_connection, base_dn,
                                             **kwargs)

        if search_scope[:3].lower() == 'sub':
            self.search_scope = ldap.SCOPE_SUBTREE
        elif search_scope[:3].lower() == 'one':
            self.search_scope = ldap.SCOPE_ONELEVEL
        else:
            raise ValueError("The search scope should be 'one[level]' or 'sub[tree]'")

        if restrict:
            self.search_pattern = u'(&%s(%s=%%s))' % (restrict,naming_attribute)
        else:
            self.search_pattern = u'(%s=%%s)' % naming_attribute

    def _get_dn(self, environ, identity):
        """
        Return the DN based on the environment and the identity.
        
        Searches the directory entry with naming attribute matching the
        C{login} item of the identity.

        If the C{login} item of the identity is C{rms}, the naming attribute is
        C{uid} and the base DN is C{dc=gnu,dc=org}, we'll ask the server
        to search for C{uid = rms} beneath the search base, hopefully 
        finding C{uid=rms,ou=developers,dc=gnu,dc=org}.
        
        @param environ: The WSGI environment.
        @param identity: The identity dictionary.
        @return: The Distinguished Name (DN)
        @rtype: C{unicode}
        @raise ValueError: If the C{login} key is not in the I{identity} dict.
        
        """

        if self.bind_dn:
            try:
                self.ldap_connection.bind_s(self.bind_dn, self.bind_password)
            except ldap.LDAPError:
                raise ValueError("Couldn't bind with supplied credentials")
        try:
            login_name = identity['login'].replace('*',r'\*')
            srch = self.search_pattern % login_name
            dn_list = self.ldap_connection.search_s(
                self.base_dn,
                self.search_scope,
                srch,
                )
            
            if len(dn_list) == 1:
                return dn_list[0][0]
            elif len(dn_list) > 1:
                raise ValueError('Too many entries found for %s' % srch)
            else:
                raise ValueError('No entry found for %s' %srch)
        except (KeyError, TypeError, ldap.LDAPError):
            raise # ValueError


#{ Metadata providers


class LDAPAttributesPlugin(object):
    """Loads LDAP attributes of the authenticated user."""
    
    implements(IMetadataProvider)

    dnrx = re.compile('<dn:(?P<b64dn>[A-Za-z0-9+/]+=*)>')
    
    def __init__(self, ldap_connection, attributes=None,
                 filterstr='(objectClass=*)', start_tls='',
                 bind_dn='', bind_pass=''):
        """
        Fetch LDAP attributes of the authenticated user.
        
        @param ldap_connection: The LDAP connection to use to fetch this data.
        @type ldap_connection: C{ldap.ldapobject.SimpleLDAPObject} or C{str}
        @param attributes: The authenticated user's LDAP attributes you want to
            use in your application; an interable or a comma-separate list of
            attributes in a string, or C{None} to fetch them all.
        @type attributes: C{iterable} or C{str}
        @param filterstr: A filter for the search, as documented in U{RFC4515
            <http://www.faqs.org/rfcs/rfc4515.html>}; the results won't be
            filtered unless you define this.
        @type filterstr: C{str}
        @param start_tls: Should we negotiate a TLS upgrade on the connection with
            the directory server?
        @type start_tls: C{str}
        @param bind_dn: Operate as the bind_dn directory entry
        @type bind_dn: C{str}
        @param bind_pass: The password for bind_dn directory entry
        @type bind_pass: C{str}
        @raise ValueError: If L{make_ldap_connection} could not create a
            connection from C{ldap_connection}, or if C{attributes} is not an
            iterable.

        The following parameters are inherited from 
        L{LDAPBaseAuthenticatorPlugin.__init__}
        @param base_dn: The base for the I{Distinguished Name}. Something like
            C{ou=employees,dc=example,dc=org}, to which will be prepended the
            user id: C{uid=jsmith,ou=employees,dc=example,dc=org}.
        @param returned_id: Should we return full Directory Names or just the
            naming attribute value on successful authentication?
        @param start_tls: Should we negotiate a TLS upgrade on the connection with
            the directory server?
        @param bind_dn: Operate as the bind_dn directory entry
        @param bind_pass: The password for bind_dn directory entry
        
        """
        if hasattr(attributes, 'split'):
            attributes = attributes.split(',')
        elif hasattr(attributes, '__iter__'):
            # Converted to list, just in case...
            attributes = list(attributes)
        elif attributes is not None:
            raise ValueError('The needed LDAP attributes are not valid')
        self.ldap_connection = make_ldap_connection(ldap_connection)
        if start_tls:
            try:
                self.ldap_connection.start_tls_s()
            except:
                raise ValueError('Cannot upgrade the connection')

        self.bind_dn   = bind_dn
        self.bind_pass = bind_pass
        self.attributes = attributes
        self.filterstr = filterstr
    
    # IMetadataProvider
    def add_metadata(self, environ, identity):
        """
        Add metadata about the authenticated user to the identity.
        
        It modifies the C{identity} dictionary to add the metadata.
        
        @param environ: The WSGI environment.
        @param identity: The repoze.who's identity dictionary.
        
        """
        # Search arguments:
        dnmatch = self.dnrx.match(identity.get('userdata',''))
        if dnmatch:
            dn = b64decode(dnmatch.group('b64dn'))
        else:
            dn = identity.get('repoze.who.userid')
        args = (
            dn,
            ldap.SCOPE_BASE,
            self.filterstr,
            self.attributes
        )
        if self.bind_dn:
            try:
                self.ldap_connection.bind_s(self.bind_dn, self.bind_pass)
            except ldap.LDAPError:
                raise ValueError("Couldn't bind with supplied credentials")
        try:
            attributes = self.ldap_connection.search_s(*args)
        except ldap.LDAPError, msg:
            environ['repoze.who.logger'].warn('Cannot add metadata: %s' % msg)
            raise Exception(identity)
        else:
            identity.update(attributes[0][1])


#{ Utilities


def make_ldap_connection(ldap_connection):
    """Return an LDAP connection object to the specified server.
    
    If the C{ldap_connection} is already an LDAP connection object, it will
    be returned as is. If it's an LDAP URL, it will return an LDAP connection
    to the LDAP server specified in the URL.
    
    @param ldap_connection: The LDAP connection object or the LDAP URL of the
        server to be connected to.
    @type ldap_connection: C{ldap.ldapobject.SimpleLDAPObject}, C{str} or
        C{unicode}
    @return: The LDAP connection object.
    @rtype: C{ldap.ldapobject.SimpleLDAPObject}
    @raise ValueError: If C{ldap_connection} is C{None}.
    
    """
    if isinstance(ldap_connection, str) or isinstance(ldap_connection, unicode):
        return ldap.initialize(ldap_connection)
    elif ldap_connection is None:
        raise ValueError('An LDAP connection must be specified')
    return ldap_connection


#}
