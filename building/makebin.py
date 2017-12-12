from cx_Freeze import setup, Executable
import sys
from defs.version import COMMIT_REVISION
build_exe_options = {"icon": "icons/icon.ico",
                     "packages": ["gui", "logic", "defs"],
                     "optimize": 2,
                     "compressed": True,
                     "include_files": "res",
                     "include_msvcr": False}
# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"
setup(
    name = "CA Control",
    version = str(COMMIT_REVISION / 10),
    description = "CA Control by XOMRKOB",
    options = {"build_exe": build_exe_options},
    executables = [Executable("main.pyw", base=base)]
)