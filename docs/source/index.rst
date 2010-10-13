===================================================================
repoze.who.plugins.ldap - LDAP Authentication for WSGI Applications
===================================================================

:Author: `Gustavo Narea <http://gustavonarea.net/>`_
:Version: |release|
:License: `Repoze <http://repoze.org/license.html>`_ (GPLv3 in v1.0).
:Homepage: http://code.gustavonarea.net/repoze.who.plugins.ldap/

.. module:: repoze.who.plugins.ldap
    :synopsis: LDAP authentication middleware for WSGI

`repoze.who.plugins.ldap <http://code.gustavonarea.net/repoze.who.plugins.ldap/>`_
is a Python package that provides `LDAP
<http://en.wikipedia.org/wiki/Lightweight_Directory_Access_Protocol>`_
authentication, and related utilities, in `WSGI
<http://en.wikipedia.org/wiki/Web_Server_Gateway_Interface>`_
applications via `repoze.who <http://static.repoze.org/whodocs/>`_. It can be 
used with any LDAP server and any WSGI framework (or no framework at all).

It provides you with an straightforward solution to enable LDAP
support in your applications. Yes, you read well: "straightforward", "LDAP" and
"applications" are in the same sentence. In fact, you may make your application
LDAP-aware in few minutes and with few lines of code.

Another great news is that this package is *fully* documented and provides you
with a working and documented demo project. 


Get started!
============

.. toctree::
    :maxdepth: 2

    Install
    Using
    Demo
    Changes

You can also browse `the online API documentation
<http://code.gustavonarea.net/repoze.who.plugins.ldap/api/>`_, or generate it
by yourself with Epydoc from the root directory of the project::

    epydoc --config=docs/epydoc.conf repoze


Links
======

If you need help, the best place to ask is `the repoze project mailing list
<http://lists.repoze.org/listinfo/repoze-dev>`_, because the plugin author is
subscribed to this list. You may also use the `#repoze
<irc://irc.freenode.net/repoze>`_ IRC channel or `Launchpad.net's answers for
quick questions only <https://answers.launchpad.net/repoze.who.plugins.ldap>`_.

Development-related links include:
 - `Homepage at Launchpad.net <https://launchpad.net/repoze.who.plugins.ldap>`_.
 - `Bug tracker <https://bugs.launchpad.net/repoze.who.plugins.ldap>`_.
 - `Feature tracker <https://blueprints.launchpad.net/repoze.who.plugins.ldap>`_.
 - `Bazaar branches <https://code.launchpad.net/repoze.who.plugins.ldap>`_.


Contributing
============

Any patch is welcome, but if you can, please make sure to update the test suite
accordingly and also make sure that every test passes. Also, please try to
stick to PEPs `8 <http://www.python.org/dev/peps/pep-0008/>`_ and `257
<http://www.python.org/dev/peps/pep-0257/>`_, as well as use `Epydoc fields
<http://epydoc.sourceforge.net/manual-fields.html>`_ where applicable.


Thanks!
=======

This plugin exists thanks to the people below:

 - **Lorenzo M. Catucci**, of the `University of Rome "Tor Vergata"
   <http://www.uniroma2.it/>`_, for implementing and documenting *all* the new
   features in v1.1.
 - **Chris McDonough**, for his guidance throughout the initial development of
   the plugin.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

