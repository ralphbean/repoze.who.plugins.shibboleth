# -*- coding: utf-8 -*-
#
# repoze.who.plugins.ldap, LDAP authentication for WSGI applications.
# Copyright (C) 2010 by Gustavo Narea  <http://gustavonarea.net/> and
#                       Lorenzo M. Catucci <http://www.uniroma2.it/>.
# Copyright (C) 2008 by Gustavo Narea <http://gustavonarea.net/>.s
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
"""Test suite for repoze.who.plugins.ldap"""

import unittest

from dataflake.ldapconnection.tests import fakeldap
import ldap
from ldap import modlist, dn
from ldap.ldapobject import SimpleLDAPObject
from zope.interface.verify import verifyClass
from repoze.who.interfaces import IAuthenticator, IMetadataProvider

from repoze.who.plugins.ldap import LDAPAuthenticatorPlugin, \
                                    LDAPAttributesPlugin, \
                                    LDAPSearchAuthenticatorPlugin
from repoze.who.plugins.ldap.plugins import make_ldap_connection

from base64 import b64encode


class Base(unittest.TestCase):
    """Base test case for the plugins"""
    
    def setUp(self):
        # Connecting to a fake server with a fake account:
        conn = fakeldap.FakeLDAPConnection()
        conn.simple_bind_s('Manager', 'some password')
        # We must explicitly create the base_dn DIT components
        fakeldap.addTreeItems(base_dn)
        # Adding a fake user, which is used in the tests
        person_attr = {'cn': [fakeuser['cn']],
                       'uid': fakeuser['uid'],
                       'userPassword': [fakeuser['hashedPassword']],
                       'telephone': [fakeuser['telephone']],
                       'mail':[fakeuser['mail']]}
        conn.add_s(fakeuser['dn'], modlist.addModlist(person_attr))
        self.connection = conn
        # Creating a fake environment:
        self.env  = self._makeEnviron()
    
    def tearDown(self):
        self.connection.delete_s(fakeuser['dn'])
    
    def _makeEnviron(self, kw=None):
        """Create a fake WSGI environment
        
        This is based on the same method of the test suite of repoze.who.
        
        """
        environ = {}
        environ['wsgi.version'] = (1,0)
        if kw is not None:
            environ.update(kw)
        return environ


#{ Test cases for the plugins


class TestMakeLDAPAuthenticatorPlugin(unittest.TestCase):
    """Tests for the constructor of the L{LDAPAuthenticatorPlugin} plugin"""
    
    def test_without_connection(self):
        self.assertRaises(ValueError, LDAPAuthenticatorPlugin, None,
                          'dc=example,dc=org')
    
    def test_without_base_dn(self):
        conn = fakeldap.FakeLDAPConnection()
        self.assertRaises(TypeError, LDAPAuthenticatorPlugin, conn)
        self.assertRaises(ValueError, LDAPAuthenticatorPlugin, conn, None)
    
    def test_with_connection(self):
        conn = fakeldap.FakeLDAPConnection()
        LDAPAuthenticatorPlugin(conn, 'dc=example,dc=org')
    
    def test_connection_is_url(self):
        LDAPAuthenticatorPlugin('ldap://example.org', 'dc=example,dc=org')


class TestLDAPAuthenticatorPlugin(Base):
    """Tests for the L{LDAPAuthenticatorPlugin} IAuthenticator plugin"""
    
    def setUp(self):
        super(TestLDAPAuthenticatorPlugin, self).setUp()
        # Loading the plugin:
        self.plugin = LDAPAuthenticatorPlugin(self.connection, base_dn)

    def test_implements(self):
        verifyClass(IAuthenticator, LDAPAuthenticatorPlugin, tentative=True)

    def test_authenticate_nologin(self):
        result = self.plugin.authenticate(self.env, None)
        self.assertEqual(result, None)

    def test_authenticate_incomplete_credentials(self):
        identity1 = {'login': fakeuser['uid']}
        identity2 = {'password': fakeuser['password']}
        result1 = self.plugin.authenticate(self.env, identity1)
        result2 = self.plugin.authenticate(self.env, identity2)
        self.assertEqual(result1, None)
        self.assertEqual(result2, None)

    def test_authenticate_noresults(self):
        identity = {'login': 'i_dont_exist',
                    'password': 'super secure password'}
        result = self.plugin.authenticate(self.env, identity)
        self.assertEqual(result, None)

    def test_authenticate_comparefail(self):
        identity = {'login': fakeuser['uid'],
                    'password': 'wrong password'}
        result = self.plugin.authenticate(self.env, identity)
        self.assertEqual(result, None)

    def test_authenticate_comparesuccess(self):
        identity = {'login': fakeuser['uid'],
                    'password': fakeuser['password']}
        result = self.plugin.authenticate(self.env, identity)
        self.assertEqual(result, fakeuser['dn'])
    
    def test_custom_authenticator(self):
        """L{LDAPAuthenticatorPlugin._get_dn} should be overriden with no
        problems"""
        plugin = CustomLDAPAuthenticatorPlugin(self.connection, base_dn)
        identity = {'login': fakeuser['uid'],
                    'password': fakeuser['password']}
        result = plugin.authenticate(self.env, identity)
        expected = 'uid=%s,%s' % (fakeuser['uid'], base_dn)
        self.assertEqual(result, expected)
        self.assertTrue(plugin.called)

class TestLDAPSearchAuthenticatorPluginNaming(Base):
    """Tests for the L{LDAPSearchAuthenticatorPlugin} IAuthenticator plugin"""
    
    def setUp(self):
        super(TestLDAPSearchAuthenticatorPluginNaming, self).setUp()
        # Loading the plugin:
        self.plugin = LDAPSearchAuthenticatorPlugin(
            self.connection,
            base_dn,
            naming_attribute='telephone',
            )

    def test_authenticate_noresults(self):
        identity = {'login': 'i_dont_exist',
                    'password': 'super secure password'}
        result = self.plugin.authenticate(self.env, identity)
        self.assertEqual(result, None)

    def test_authenticate_comparefail(self):
        identity = {'login': fakeuser['telephone'],
                    'password': 'wrong password'}
        result = self.plugin.authenticate(self.env, identity)
        self.assertEqual(result, None)

    def test_authenticate_comparesuccess(self):
        identity = {'login': fakeuser['telephone'],
                    'password': fakeuser['password']}
        result = self.plugin.authenticate(self.env, identity)
        self.assertEqual(result, fakeuser['dn'])
    
class TestLDAPAuthenticatorReturnLogin(Base):
    """
    Tests the L{LDAPAuthenticatorPlugin} IAuthenticator plugin returning
    login.
    
    """
    
    def setUp(self):
        super(TestLDAPAuthenticatorReturnLogin, self).setUp()
        # Loading the plugin:
        self.plugin = LDAPAuthenticatorPlugin(
            self.connection,
            base_dn,
            returned_id='login',
            )

    def test_authenticate_noresults(self):
        identity = {'login': 'i_dont_exist',
                    'password': 'super secure password'}
        result = self.plugin.authenticate(self.env, identity)
        self.assertEqual(result, None)

    def test_authenticate_comparefail(self):
        identity = {'login': fakeuser['uid'],
                    'password': 'wrong password'}
        result = self.plugin.authenticate(self.env, identity)
        self.assertEqual(result, None)

    def test_authenticate_comparesuccess(self):
        identity = {'login': fakeuser['uid'],
                    'password': fakeuser['password']}
        result = self.plugin.authenticate(self.env, identity)
        self.assertEqual(result, fakeuser['uid'])

    def test_authenticate_dn_in_userdata(self):
        identity = {'login': fakeuser['uid'],
                    'password': fakeuser['password']}
        expected_dn = '<dn:%s>' % b64encode(fakeuser['dn'])
        result = self.plugin.authenticate(self.env, identity)
        self.assertEqual(identity['userdata'], expected_dn)
        
    
class TestLDAPSearchAuthenticatorReturnLogin(Base):
    """
    Tests the L{LDAPSearchAuthenticatorPlugin} IAuthenticator plugin returning
    login.
    
    """
    
    def setUp(self):
        super(TestLDAPSearchAuthenticatorReturnLogin, self).setUp()
        # Loading the plugin:
        self.plugin = LDAPSearchAuthenticatorPlugin(
            self.connection,
            base_dn,
            returned_id='login',
            )

    def test_authenticate_noresults(self):
        identity = {'login': 'i_dont_exist',
                    'password': 'super secure password'}
        result = self.plugin.authenticate(self.env, identity)
        self.assertEqual(result, None)

    def test_authenticate_comparefail(self):
        identity = {'login': fakeuser['uid'],
                    'password': 'wrong password'}
        result = self.plugin.authenticate(self.env, identity)
        self.assertEqual(result, None)

    def test_authenticate_comparesuccess(self):
        identity = {'login': fakeuser['uid'],
                    'password': fakeuser['password']}
        result = self.plugin.authenticate(self.env, identity)
        self.assertEqual(result, fakeuser['uid'])

    def test_authenticate_dn_in_userdata(self):
        identity = {'login': fakeuser['uid'],
                    'password': fakeuser['password']}
        expected_dn = '<dn:%s>' % b64encode(fakeuser['dn'])
        result = self.plugin.authenticate(self.env, identity)
        self.assertEqual(identity['userdata'], expected_dn)
        
    
class TestLDAPAuthenticatorPluginStartTls(Base):
    """Tests for the L{LDAPAuthenticatorPlugin} IAuthenticator plugin"""
    
    def setUp(self):
        super(TestLDAPAuthenticatorPluginStartTls, self).setUp()
        # Loading the plugin:
        self.plugin = LDAPAuthenticatorPlugin(self.connection, base_dn,
                                              start_tls=True)

    def test_implements(self):
        verifyClass(IAuthenticator, LDAPAuthenticatorPlugin, tentative=True)


class TestMakeLDAPAttributesPlugin(unittest.TestCase):
    """Tests for the constructor of L{LDAPAttributesPlugin}"""
    
    def test_connection_is_invalid(self):
        self.assertRaises(ValueError, LDAPAttributesPlugin, None, 'cn')
    
    def test_attributes_is_none(self):
        """If attributes is None then fetch all the attributes"""
        plugin = LDAPAttributesPlugin('ldap://localhost', None)
        self.assertEqual(plugin.attributes, None)
    
    def test_attributes_is_comma_separated_str(self):
        attributes = "cn,uid,mail"
        plugin = LDAPAttributesPlugin('ldap://localhost', attributes)
        self.assertEqual(plugin.attributes, attributes.split(','))
    
    def test_attributes_is_only_one_as_str(self):
        attributes = "mail"
        plugin = LDAPAttributesPlugin('ldap://localhost', attributes)
        self.assertEqual(plugin.attributes, ['mail'])
    
    def test_attributes_is_iterable(self):
        # The plugin, with a tuple as attributes
        attributes_t = ('cn', 'mail')
        plugin_t = LDAPAttributesPlugin('ldap://localhost', attributes_t)
        self.assertEqual(plugin_t.attributes, list(attributes_t))
        # The plugin, with a list as attributes
        attributes_l = ['cn', 'mail']
        plugin_l = LDAPAttributesPlugin('ldap://localhost', attributes_l)
        self.assertEqual(plugin_l.attributes, attributes_l)
        # The plugin, with a dict as attributes
        attributes_d = {'first': 'cn', 'second': 'mail'}
        plugin_d = LDAPAttributesPlugin('ldap://localhost', attributes_d)
        self.assertEqual(plugin_d.attributes, list(attributes_d))
    
    def test_attributes_is_not_iterable_nor_string(self):
        self.assertRaises(ValueError, LDAPAttributesPlugin, 'ldap://localhost',
                          12345)
    
    def test_parameters_are_valid(self):
        LDAPAttributesPlugin('ldap://localhost', 'cn', '(objectClass=*)')


class TestLDAPAttributesPlugin(Base):
    """Tests for the L{LDAPAttributesPlugin} IMetadata plugin"""

    def test_implements(self):
        verifyClass(IMetadataProvider, LDAPAttributesPlugin, tentative=True)

    def test_add_metadata(self):
        plugin = LDAPAttributesPlugin(self.connection)
        environ = {}
        identity = {'repoze.who.userid': fakeuser['dn']}
        expected_identity = {
            'repoze.who.userid': fakeuser['dn'],
            'cn': [fakeuser['cn']],
            'userPassword': [fakeuser['hashedPassword']],
            'uid': fakeuser['uid'],
            'telephone': [ fakeuser['telephone']],
            'mail': [fakeuser['mail']]
        }
        plugin.add_metadata(environ, identity)
        self.assertEqual(identity, expected_identity)


# Test cases for plugin utilities

class TestLDAPConnectionFactory(unittest.TestCase):
    """Tests for L{make_ldap_connection}"""
    
    def test_connection_is_object(self):
        conn = fakeldap.FakeLDAPConnection()
        self.assertEqual(make_ldap_connection(conn), conn)
    
    def test_connection_is_str(self):
        conn = make_ldap_connection('ldap://example.org')
        self.assertTrue(isinstance(conn, SimpleLDAPObject))
    
    def test_connection_is_unicode(self):
        conn = make_ldap_connection(u'ldap://example.org')
        self.assertTrue(isinstance(conn, SimpleLDAPObject))
    
    def test_connection_is_none(self):
        self.assertRaises(ValueError, make_ldap_connection, None)


# Test cases for the fakeldap connection itself

class TestLDAPConnection(unittest.TestCase):
    """Connection use tests"""
    
    def setUp(self):
        # Connecting to a fake server with a fake account:
        conn = fakeldap.FakeLDAPConnection()
        conn.simple_bind_s('Manager', 'some password')
        # We must explicitly create the base_dn DIT components
        fakeldap.addTreeItems(base_dn)
        # Adding a fake user, which is used in the tests
        self.person_attr = {'cn': [fakeuser['cn']],
                       'uid': fakeuser['uid'],
                       'userPassword': [fakeuser['hashedPassword']],
                       'telephone':[fakeuser['telephone']],
                       'objectClass': ['top']}
        conn.add_s(fakeuser['dn'], modlist.addModlist(self.person_attr))
        self.connection = conn

    def tearDown(self):
        self.connection.delete_s(fakeuser['dn'])

    def test_simple_search_result(self):
        rs = self.connection.search_s(
            base_dn,
            ldap.SCOPE_SUBTREE,
            '(uid=%s)' % fakeuser['uid'],
            )
        self.assertEqual(rs[0][0], fakeuser['dn'])
        self.assertEqual(rs[0][1], self.person_attr )

    def unimplemented_test_and_search_result(self):
        rs = self.connection.search_s(
            base_dn,
            ldap.SCOPE_SUBTREE,
            '(&(objectclass=*)(uid=%s))' % fakeuser['uid'],
            )
        self.assertEqual(rs[0][0], fakeuser['dn'])
        self.assertEqual(rs[0][1], self.person_attr )

    def unimplemented_test_bare_search_result(self):
        rs = self.connection.search_s(
            base_dn,
            ldap.SCOPE_SUBTREE,
            'uid=%s' % fakeuser['uid'],
            )
        self.assertEqual(rs[0][0], fakeuser['dn'])
        self.assertEqual(rs[0][1], self.person_attr )

    def error_test_email_address_search(self):
        rs = self.connection.search_s(
            base_dn,
            ldap.SCOPE_SUBTREE,
            '(mail=%s)' % fakeuser['mail'],
            )
        self.assertEqual(rs[0][0], fakeuser['dn'])
        self.assertEqual(rs[0][1], self.person_attr )

    def error_test_plus_in_search(self):
        rs = self.connection.search_s(
            base_dn,
            ldap.SCOPE_SUBTREE,
            '(telephone=+%s)' % fakeuser['telephone'],
            )
        self.assertEqual(rs[0][0], fakeuser['dn'])
        self.assertEqual(rs[0][1], self.person_attr )

#{ Fixtures

base_dn = 'ou=people,dc=example,dc=org'
    
fakeuser = {
    'dn': 'uid=carla,%s' % base_dn,
    'uid': 'carla',
    'cn': 'Carla Paola',
    'mail': 'carla@example.org',
    'telephone': '39 123 456 789',
    'password': 'hello',
    'hashedPassword': '{SHA}qvTGHdzF6KLavt4PO0gs2a6pQ00='
}


class CustomLDAPAuthenticatorPlugin(LDAPAuthenticatorPlugin):
    """Fake class to test that L{LDAPAuthenticatorPlugin._get_dn} can be
    overriden with no problems"""
    
    def _get_dn(self, environ, identity):
        self.called = True
        try:
            return u'uid=%s,%s' % (identity['login'], self.base_dn)
        except (KeyError, TypeError):
            raise ValueError, ('Could not find the DN from the identity and '
                               'environment')


#}


def suite():
    """
    Return the test suite.
    
    @return: The test suite for the plugin.
    @rtype: C{unittest.TestSuite}
    
    """
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestLDAPConnection, "test"))
    suite.addTest(unittest.makeSuite(TestMakeLDAPAuthenticatorPlugin, "test"))
    suite.addTest(unittest.makeSuite(TestLDAPAuthenticatorPlugin, "test"))
    suite.addTest(unittest.makeSuite(TestMakeLDAPAttributesPlugin, "test"))
    suite.addTest(unittest.makeSuite(TestLDAPAttributesPlugin, "test"))
    suite.addTest(unittest.makeSuite(TestLDAPConnectionFactory, "test"))
    suite.addTest(unittest.makeSuite(TestLDAPSearchAuthenticatorPluginNaming,
                                     "test"))
    suite.addTest(unittest.makeSuite(TestLDAPAuthenticatorReturnLogin, "test"))
    suite.addTest(unittest.makeSuite(TestLDAPSearchAuthenticatorReturnLogin,
                                     "test"))
    suite.addTest(unittest.makeSuite(TestLDAPAuthenticatorPluginStartTls,
                                     "test"))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
