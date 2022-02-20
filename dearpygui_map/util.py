"""Utility functions"""

import platform
from pathlib import Path


def user_cache_dir():
    r"""Return path to application cache directory

    For different platforms, cache directories are:
        Windows:    C:\Users\<username>\AppData\Local\dearpygui_map\Cache
        Mac OS X:   ~/Library/Caches/dearpygui_map
        Unix:       ~/.cache/dearpygui_map
    """
    app_name = "dearpygui_map"
    if platform.system() == "Windows":
        return Path.home() / "AppData" / "Local" / app_name / "Cache"
    elif platform.system() == "Darwin":
        return Path.home() / "Library" / "Caches" / app_name
    else:
        return Path.home() / ".cache" / app_name
