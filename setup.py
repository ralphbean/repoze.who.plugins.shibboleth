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

import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README')).read()
CHANGELOG = open(os.path.join(here, "docs", "source", 'Changes.rst')).read()
version = open(os.path.join(here, 'VERSION')).readline().rstrip()

setup(
    name='repoze.who.plugins.ldap',
    version=version,
    description="LDAP plugin for repoze.who",
    long_description='\n\n'.join([README, CHANGELOG]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware",
        "Topic :: System :: Systems Administration :: Authentication/Directory :: LDAP"
    ],
    keywords='ldap web application server wsgi repoze repoze.who',
    author="Gustavo Narea",
    author_email="me@gustavonarea.net",
    url="http://code.gustavonarea.net/repoze.who.plugins.ldap/",
    download_url="https://launchpad.net/repoze.who.plugins.ldap/+download",
    license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
    include_package_data=True,
    packages=find_packages(exclude=["*.tests", "demo", "demo.*"]),
    namespace_packages=['repoze', 'repoze.who', 'repoze.who.plugins'],
    zip_safe=False,
    tests_require = ['dataflake.ldapconnection < 1.1dev'],
    install_requires=[
        'repoze.who >= 1.0.6, < 2.0dev',
        'python-ldap>=2.3.5',
        'setuptools',
        'zope.interface'
        ],
    test_suite="repoze.who.plugins.ldap.tests.suite"
    )
