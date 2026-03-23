"""
Creates symlinks for all mods without touching any other files.
Run from an admin terminal: python Setup/link_only.py
"""

import os
import sys
import glob
import platform

PROFILE_NAME = "h2-dev"
SETUP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SETUP_DIR)

if platform.system() == "Windows":
    appdata = os.environ.get("APPDATA")
    PROFILE_PATH = os.path.join(appdata, "r2modmanPlus-local", "HadesII", "profiles", PROFILE_NAME, "ReturnOfModding")
else:
    PROFILE_PATH = os.path.expanduser(f"~/.config/r2modmanPlus-local/HadesII/profiles/{PROFILE_NAME}/ReturnOfModding")


def get_mod_name(toml_path):
    namespace, name = None, None
    with open(toml_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('namespace ='):
                namespace = line.split('=')[1].strip().strip('"\'')
            elif line.startswith('name ='):
                name = line.split('=')[1].strip().strip('"\'')
    if namespace and name:
        return f"{namespace}-{name}"
    return None


def create_link(target, link_path):
    if not os.path.isdir(target):
        return
    if os.path.exists(link_path) or os.path.lexists(link_path):
        print(f"  EXISTS: {link_path}")
        return
    os.symlink(os.path.abspath(target), os.path.abspath(link_path), target_is_directory=True)
    print(f"  LINKED: {link_path}")


def main():
    print(f"\nSymlink-only deployment to profile: {PROFILE_NAME}\n")

    targets = [
        os.path.join(ROOT_DIR, "adamant-modpack-Core"),
        os.path.join(ROOT_DIR, "adamant-modpack-Lib"),
    ] + sorted(glob.glob(os.path.join(ROOT_DIR, "Submodules", "adamant-*")))

    count = 0
    for mod_dir in targets:
        toml_path = os.path.join(mod_dir, "thunderstore.toml")
        if not os.path.isfile(toml_path):
            continue

        mod_name = get_mod_name(toml_path)
        if not mod_name:
            print(f"SKIP: {mod_dir}")
            continue

        print(f"--- {mod_name} ---")
        create_link(os.path.join(mod_dir, "src"), os.path.join(PROFILE_PATH, "plugins", mod_name))
        create_link(os.path.join(mod_dir, "data"), os.path.join(PROFILE_PATH, "plugins_data", mod_name))
        count += 1

    print(f"\nDone. {count} mods processed.\n")


if __name__ == "__main__":
    main()
