import os
from gen_version import create_version_file
from shutil import copytree, rmtree
from os.path import splitext, join
from os import walk
print(">> Generating version")
create_version_file('defs'+os.sep+'version.py')
WORKING_DIR = 'building'
print(">> Preparing working dir: {}".format(WORKING_DIR))
if os.path.exists(WORKING_DIR):
    rmtree(WORKING_DIR)
# Copy current dir to working
copytree('.', WORKING_DIR)
os.chdir(WORKING_DIR)
print(">> Compiling py to cython")
os.system('python compile.py build_ext  --inplace')
for root, _, files in walk('.'):
    for file in files:
        if (splitext(file)[1].lower() == '.py' and file != '__init__.py' and root != '.')\
                or splitext(file)[1].lower() == '.c'\
                or splitext(file)[1].lower() == '.pyc':
            print("Removing src file: {}".format(join(root, file)))
            os.remove(join(root, file))
print(">> Building release with cxFreeze")
os.system('python makebin.py build')