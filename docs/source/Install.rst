==================================
Installing repoze.who.plugins.ldap
==================================

Installing the `repoze.who.plugins.ldap
<http://code.gustavonarea.net/repoze.who.plugins.ldap/>`_ plugin itself is
rather easy, but unfortunately, installing `python-ldap
<http://python-ldap.sourceforge.net/>`_ (the main dependency of this plugin)
may be a nightmare. Hopefully this document will help you get this plugin
and its dependencies working quickly.

The quick install
==================

If you've already installed `python-ldap` on your computer, the following
command will install `repoze.who.plugins.ldap`::

    easy_install repoze.who.plugins.ldap

If it's not already installed on your computer, read on.

**Note:** If you're on Ubuntu, don't rely on the python-ldap package provided by
the package manager - `its install will be ignored by easy_install for some
reason <https://bugs.launchpad.net/ubuntu/+source/python-ldap/+bug/267193>`_;
this may also happen in Debian. Read on to install it manually.


Installing `python-ldap` manually
=================================

If you have problems to install the plugin, they are very likely to be caused by
`python-ldap`: You will have to install it manually in order to set the correct
path to the OpenLDAP libraries.

Once you've successfully installed `python-ldap`, you'll be ready to install
`repoze.who.plugins.ldap` with the command above.

Installing `python-ldap` on Ubuntu
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This may also work for Debian. If this procedure works in your Debian system,
please let us know.

First, install its dependencies::

    sudo apt-get install build-essential libldap2-dev libsasl2-dev python-dev libssl-dev

Then, download the source of `python-ldap`, uncompress it and `cd` to its folder.
Once you're there, edit the `setup.cfg` file to correct the parameters in the
`[_ldap]` section::

    extra_objects =
    extra_compile_args =
    libs = ldap_r lber ssl crypto
    library_dirs = /usr/lib
    include_dirs = /usr/include /usr/lib/sasl2

Save the file and run::

    python setup.py build
    sudo python setup.py install


Installing on other systems
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For more information, visit:
http://python-ldap.sourceforge.net/doc/html/installing.html

Please don't hesitate to let us know how you installed it on other systems, so
that we can post it here.

Troubleshooting
~~~~~~~~~~~~~~~~

If you have trouble to install `python-ldap` on your system, please ask in `the
python-ldap mailing list
<https://lists.sourceforge.net/lists/listinfo/python-ldap-dev>`_.


Installing the mainline development branch
==========================================

The plugin is hosted in `a Bazaar branch hosted at Launchpad.net
<https://code.launchpad.net/repoze.who.plugins.ldap>`_. To get the latest source
code, run::

    bzr branch lp:repoze.who.plugins.ldap

Then run the command below, from the project folder::

    python setup.py develop
