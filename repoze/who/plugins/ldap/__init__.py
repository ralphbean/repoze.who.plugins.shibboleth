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

"""repoze.who LDAP plugin

U{repoze.who.plugins.ldap <http://code.gustavonarea.net/repoze.who.plugins.ldap/>}
is a Python package that provides U{repoze.who 
<http://static.repoze.org/whodocs/>} plugins for U{LDAP 
<http://en.wikipedia.org/wiki/Lightweight_Directory_Access_Protocol>}
authentication in U{WSGI 
<http://en.wikipedia.org/wiki/Web_Server_Gateway_Interface>}
applications. It can be used with any LDAP server and any WSGI framework (or no
framework at all).

For information on how to get started, you may want to visit its web site:
U{http://code.gustavonarea.net/repoze.who.plugins.ldap/}

G{packagetree}

"""

import ldap

from repoze.who.plugins.ldap.plugins import LDAPBaseAuthenticatorPlugin, \
                                            LDAPAuthenticatorPlugin, \
                                            LDAPAttributesPlugin, \
                                            LDAPSearchAuthenticatorPlugin

__all__ = ['LDAPAuthenticatorPlugin', 'LDAPSearchAuthenticatorPlugin', 'LDAPAttributesPlugin']
