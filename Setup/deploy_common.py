"""
Shared utilities for deploy_* scripts.
"""

import os
import glob
import argparse
import platform


SETUP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SETUP_DIR)
DEFAULT_PROFILE = "h2-dev"


def get_profile_path(profile_name):
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA")
        return os.path.join(appdata, "r2modmanPlus-local", "HadesII", "profiles", profile_name, "ReturnOfModding")
    else:
        return os.path.expanduser(f"~/.config/r2modmanPlus-local/HadesII/profiles/{profile_name}/ReturnOfModding")


def get_toml_info(toml_path):
    namespace, name = None, None
    with open(toml_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('namespace ='):
                namespace = line.split('=')[1].strip().strip('"\'')
            elif line.startswith('name ='):
                name = line.split('=')[1].strip().strip('"\'')
    return namespace, name


def discover_mods():
    """Returns list of mod directories (Lib, Framework, Core, then Submodules/adamant-*)."""
    targets = [
        os.path.join(ROOT_DIR, "adamant-modpack-Lib"),
        os.path.join(ROOT_DIR, "adamant-modpack-Framework"),
        os.path.join(ROOT_DIR, "adamant-modpack-coordinator"),
    ] + sorted(glob.glob(os.path.join(ROOT_DIR, "Submodules", "adamant-*")))
    return [d for d in targets if os.path.isfile(os.path.join(d, "thunderstore.toml"))]


def base_parser(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files/links (default: skip)")
    parser.add_argument("--profile", default=DEFAULT_PROFILE, help=f"r2modman profile name (default: {DEFAULT_PROFILE})")
    return parser
