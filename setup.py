
from cx_Freeze import setup, Executable

build_options = {
    "packages": [
        "pygame"
    ],

    "include_files": [
        ("gleb.mp3", "gleb.mp3")
    ],

    "include_msvcr": True,
}

exe = Executable(
    script="SafeUnlock.py",
    target_name="SafeUnlock.exe",
    base=None
)

setup(
    name="SafeUnlock",
    version="1.0.1",
    description="Windows Recovery Utility",

    options={
        "build_exe": build_options
    },

    executables=[exe]
)
