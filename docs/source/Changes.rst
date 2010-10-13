repoze.who.plugins.ldap Changelog
=================================

1.1 Alpha 1 (2010-01-03)
------------------------


 - Changed the license to the `Repoze license <http://repoze.org/license.html>`_.
 - Provided ``start_tls`` option both for the authenticator and the metadata
   provider.
 - Enable both pattern-replacement and subtree searches for the naming
   attribute in ``_get_dn()``.
 - Enable configuration of the naming attribute
 - Enable the option to bind to the server with privileged credential before
   doing searches
 - Add a restrict pattern to pre-authentication DN searches
 - Let the user choose whether to return the full DN or the supplied login as
   the user identifier


1.0 (2008-09-11)
----------------

The initial release.

 - Provided the LDAP authenticator, which is compatible with identifiers that
   define the 'login' item in the identity dict.
 - Included the plugin to load metadata about the authenticated user from the
   LDAP server.
 - Documented how to install and use the plugins.
 - Included Turbogears 2 demo project, using the plugin. There is also a section
   in the documentation to explain how the demo works.
