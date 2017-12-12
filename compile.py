# -*- coding: utf-8 -*-
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from os import walk
from os.path import splitext, join, sep
"""
find all .py files in subfolders
"""
def cython_file_list():
    files_for_cython = []
    for root, _, files in walk('.'):
        for file in files:
            if splitext(file)[1].lower() == '.py' and file != '__init__.py' and root != '.':
                files_for_cython.append(join(root, file))
    return files_for_cython
"""
Determine file path in "package" format. 
For example '.\generic\vesion.py' will have path 'generic.version'
"""
def ext_pack_name(filename):
    return filename[2:].replace('.py','').replace(sep, '.')
files = cython_file_list()
ext_modules = []
for f in files:
    print("Add to compile list {}".format(f))
    ext_modules.append(Extension(ext_pack_name(f), [f[2:]]))
setup(
    name = 'CA Control',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules
)