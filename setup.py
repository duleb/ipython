#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script for IPython.

Under Posix environments it works like a typical setup.py script.
Under Windows, the command sdist is not supported, since IPython
requires utilities which are not available under Windows."""

#-----------------------------------------------------------------------------
#  Copyright (c) 2008-2011, IPython Development Team.
#  Copyright (c) 2001-2007, Fernando Perez <fernando.perez@colorado.edu>
#  Copyright (c) 2001, Janko Hauser <jhauser@zscout.de>
#  Copyright (c) 2001, Nathaniel Gray <n8gray@caltech.edu>
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.rst, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Minimal Python version sanity check
#-----------------------------------------------------------------------------
from __future__ import print_function

import sys

# This check is also made in IPython/__init__, don't forget to update both when
# changing Python version requirements.
v = sys.version_info
if v[:2] < (2,7) or (v[0] >= 3 and v[:2] < (3,3)):
    error = "ERROR: IPython requires Python version 2.7 or 3.3 or above."
    print(error, file=sys.stderr)
    sys.exit(1)

PY3 = (sys.version_info[0] >= 3)

# At least we're on the python version we need, move on.

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

# Stdlib imports
import os
import shutil

from glob import glob

# BEFORE importing distutils, remove MANIFEST. distutils doesn't properly
# update it when the contents of directories change.
if os.path.exists('MANIFEST'): os.remove('MANIFEST')

from distutils.core import setup

# Our own imports
from setupbase import target_update

from setupbase import (
    setup_args,
    find_packages,
    find_package_data,
    check_package_data_first,
    find_entry_points,
    build_scripts_entrypt,
    find_data_files,
    check_for_dependencies,
    git_prebuild,
    check_submodule_status,
    update_submodules,
    require_submodules,
    UpdateSubmodules,
    get_bdist_wheel,
    CompileCSS,
    JavascriptVersion,
    install_symlinked,
    install_lib_symlink,
    install_scripts_for_symlink,
    unsymlink,
)
from setupext import setupext

isfile = os.path.isfile
pjoin = os.path.join

#-----------------------------------------------------------------------------
# Function definitions
#-----------------------------------------------------------------------------

def cleanup():
    """Clean up the junk left around by the build process"""
    if "develop" not in sys.argv and "egg_info" not in sys.argv:
        try:
            shutil.rmtree('ipython.egg-info')
        except:
            try:
                os.unlink('ipython.egg-info')
            except:
                pass

#-------------------------------------------------------------------------------
# Handle OS specific things
#-------------------------------------------------------------------------------

if os.name in ('nt','dos'):
    os_name = 'windows'
else:
    os_name = os.name

# Under Windows, 'sdist' has not been supported.  Now that the docs build with
# Sphinx it might work, but let's not turn it on until someone confirms that it
# actually works.
if os_name == 'windows' and 'sdist' in sys.argv:
    print('The sdist command is not available under Windows.  Exiting.')
    sys.exit(1)

#-------------------------------------------------------------------------------
# Make sure we aren't trying to run without submodules
#-------------------------------------------------------------------------------
here = os.path.abspath(os.path.dirname(__file__))

def require_clean_submodules():
    """Check on git submodules before distutils can do anything

    Since distutils cannot be trusted to update the tree
    after everything has been set in motion,
    this is not a distutils command.
    """
    # PACKAGERS: Add a return here to skip checks for git submodules
    
    # don't do anything if nothing is actually supposed to happen
    for do_nothing in ('-h', '--help', '--help-commands', 'clean', 'submodule'):
        if do_nothing in sys.argv:
            return

    status = check_submodule_status(here)

    if status == "missing":
        print("checking out submodules for the first time")
        update_submodules(here)
    elif status == "unclean":
        print('\n'.join([
            "Cannot build / install IPython with unclean submodules",
            "Please update submodules with",
            "    python setup.py submodule",
            "or",
            "    git submodule update",
            "or commit any submodule changes you have made."
        ]))
        sys.exit(1)

require_clean_submodules()

#-------------------------------------------------------------------------------
# Things related to the IPython documentation
#-------------------------------------------------------------------------------

# update the manuals when building a source dist
if len(sys.argv) >= 2 and sys.argv[1] in ('sdist','bdist_rpm'):

    # List of things to be updated. Each entry is a triplet of args for
    # target_update()
    to_update = [
                  # FIXME - Disabled for now: we need to redo an automatic way
                  # of generating the magic info inside the rst.
                  #('docs/magic.tex',
                  #['IPython/Magic.py'],
                  #"cd doc && ./update_magic.sh" ),

                 ('docs/man/ipcluster.1.gz',
                  ['docs/man/ipcluster.1'],
                  'cd docs/man && gzip -9c ipcluster.1 > ipcluster.1.gz'),

                 ('docs/man/ipcontroller.1.gz',
                  ['docs/man/ipcontroller.1'],
                  'cd docs/man && gzip -9c ipcontroller.1 > ipcontroller.1.gz'),

                 ('docs/man/ipengine.1.gz',
                  ['docs/man/ipengine.1'],
                  'cd docs/man && gzip -9c ipengine.1 > ipengine.1.gz'),

                 ('docs/man/ipython.1.gz',
                  ['docs/man/ipython.1'],
                  'cd docs/man && gzip -9c ipython.1 > ipython.1.gz'),

                 ]


    [ target_update(*t) for t in to_update ]

#---------------------------------------------------------------------------
# Find all the packages, package data, and data_files
#---------------------------------------------------------------------------

packages = find_packages()
package_data = find_package_data()

data_files = find_data_files()

setup_args['packages'] = packages
setup_args['package_data'] = package_data
setup_args['data_files'] = data_files

#---------------------------------------------------------------------------
# custom distutils commands
#---------------------------------------------------------------------------
# imports here, so they are after setuptools import if there was one
from distutils.command.sdist import sdist
from distutils.command.upload import upload

class UploadWindowsInstallers(upload):

    description = "Upload Windows installers to PyPI (only used from tools/release_windows.py)"
    user_options = upload.user_options + [
        ('files=', 'f', 'exe file (or glob) to upload')
    ]
    def initialize_options(self):
        upload.initialize_options(self)
        meta = self.distribution.metadata
        base = '{name}-{version}'.format(
            name=meta.get_name(),
            version=meta.get_version()
        )
        self.files = os.path.join('dist', '%s.*.exe' % base)

    def run(self):
        for dist_file in glob(self.files):
            self.upload_file('bdist_wininst', 'any', dist_file)

setup_args['cmdclass'] = {
    'build_py': check_package_data_first(git_prebuild('IPython')),
    'sdist' : git_prebuild('IPython', sdist),
    'upload_wininst' : UploadWindowsInstallers,
    'submodule' : UpdateSubmodules,
    'css' : CompileCSS,
    'symlink': install_symlinked,
    'install_lib_symlink': install_lib_symlink,
    'install_scripts_sym': install_scripts_for_symlink,
    'unsymlink': unsymlink,
    'jsversion' : JavascriptVersion,
}

#---------------------------------------------------------------------------
# Handle scripts, dependencies, and setuptools specific things
#---------------------------------------------------------------------------

# For some commands, use setuptools.  Note that we do NOT list install here!
# If you want a setuptools-enhanced install, just run 'setupegg.py install'
needs_setuptools = set(('develop', 'release', 'bdist_egg', 'bdist_rpm',
           'bdist', 'bdist_dumb', 'bdist_wininst', 'bdist_wheel',
           'egg_info', 'easy_install', 'upload', 'install_egg_info',
            ))
if sys.platform == 'win32':
    # Depend on setuptools for install on *Windows only*
    # If we get script-installation working without setuptools,
    # then we can back off, but until then use it.
    # See Issue #369 on GitHub for more
    needs_setuptools.add('install')

if len(needs_setuptools.intersection(sys.argv)) > 0:
    import setuptools

# This dict is used for passing extra arguments that are setuptools
# specific to setup
setuptools_extra_args = {}

# setuptools requirements

extras_require = dict(
    parallel = ['pyzmq>=2.1.11'],
    qtconsole = ['pyzmq>=2.1.11', 'pygments'],
    zmq = ['pyzmq>=2.1.11'],
    doc = ['Sphinx>=1.1', 'numpydoc'],
    test = ['nose>=0.10.1'],
    terminal = [],
    notebook = ['tornado>=3.1', 'pyzmq>=2.1.11', 'jinja2'],
    nbconvert = ['pygments', 'jinja2', 'Sphinx>=0.3']
)
if sys.version_info < (3, 3):
    extras_require['test'].append('mock')

everything = set()
for deps in extras_require.values():
    everything.update(deps)
extras_require['all'] = everything

install_requires = []

# add readline
if sys.platform == 'darwin':
    if any(arg.startswith('bdist') for arg in sys.argv) or not setupext.check_for_readline():
        install_requires.append('gnureadline')
elif sys.platform.startswith('win'):
    extras_require['terminal'].append('pyreadline>=2.0')


if 'setuptools' in sys.modules:
    # setup.py develop should check for submodules
    from setuptools.command.develop import develop
    setup_args['cmdclass']['develop'] = require_submodules(develop)
    setup_args['cmdclass']['bdist_wheel'] = get_bdist_wheel()
    
    setuptools_extra_args['zip_safe'] = False
    setuptools_extra_args['entry_points'] = {'console_scripts':find_entry_points()}
    setup_args['extras_require'] = extras_require
    requires = setup_args['install_requires'] = install_requires

    # Script to be run by the windows binary installer after the default setup
    # routine, to add shortcuts and similar windows-only things.  Windows
    # post-install scripts MUST reside in the scripts/ dir, otherwise distutils
    # doesn't find them.
    if 'bdist_wininst' in sys.argv:
        if len(sys.argv) > 2 and \
               ('sdist' in sys.argv or 'bdist_rpm' in sys.argv):
            print >> sys.stderr, "ERROR: bdist_wininst must be run alone. Exiting."
            sys.exit(1)
        setup_args['data_files'].append(
            ['Scripts', ('scripts/ipython.ico', 'scripts/ipython_nb.ico')])
        setup_args['scripts'] = [pjoin('scripts','ipython_win_post_install.py')]
        setup_args['options'] = {"bdist_wininst":
                                 {"install_script":
                                  "ipython_win_post_install.py"}}

else:
    # If we are installing without setuptools, call this function which will
    # check for dependencies an inform the user what is needed.  This is
    # just to make life easy for users.
    for install_cmd in ('install', 'symlink'):
        if install_cmd in sys.argv:
            check_for_dependencies()
            break
    # scripts has to be a non-empty list, or install_scripts isn't called
    setup_args['scripts'] = [e.split('=')[0].strip() for e in find_entry_points()]

    setup_args['cmdclass']['build_scripts'] = build_scripts_entrypt

#---------------------------------------------------------------------------
# Do the actual setup now
#---------------------------------------------------------------------------

setup_args.update(setuptools_extra_args)

def main():
    setup(**setup_args)
    cleanup()

if __name__ == '__main__':
    main()
