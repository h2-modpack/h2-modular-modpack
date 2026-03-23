import os
import sys
import glob
import shutil
import platform
import subprocess

# --- 1. Configuration & Pathing ---
PROFILE_NAME = "h2-dev"

# Step out of the 'Setup' folder to find the project root
SETUP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SETUP_DIR) 

# Cross-platform profile resolution
if platform.system() == "Windows":
    appdata = os.environ.get("APPDATA")
    PROFILE_PATH = os.path.join(appdata, "r2modmanPlus-local", "HadesII", "profiles", PROFILE_NAME, "ReturnOfModding")
else:
    PROFILE_PATH = os.path.expanduser(f"~/.config/r2modmanPlus-local/HadesII/profiles/{PROFILE_NAME}/ReturnOfModding")

print("\n==========================================================")
print("  Adamant Modpack - Full Local Deployment")
print(f"  Profile: {PROFILE_NAME}")
print("==========================================================\n")

# --- 2. Helper: Basic TOML Parser ---
def get_toml_info(toml_path):
    namespace, name = None, None
    with open(toml_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('namespace ='):
                namespace = line.split('=')[1].strip().strip('"\'')
            elif line.startswith('name ='):
                name = line.split('=')[1].strip().strip('"\'')
    return namespace, name

# --- 3. Main Deployment Logic ---
def setup_mod(mod_dir):
    toml_file = os.path.join(mod_dir, "thunderstore.toml")
    
    namespace, name = get_toml_info(toml_file)
    if not namespace or not name:
        print(f"SKIP: Could not parse namespace/name from {toml_file}")
        return False
        
    mod_name = f"{namespace}-{name}"
    print(f"--- Setting up: {mod_name} ---")
    
    src_dir = os.path.join(mod_dir, "src")
    data_dir = os.path.join(mod_dir, "data")
    
    # Copy static assets (Pulling from SETUP_DIR, not ROOT_DIR)
    for asset in ["icon.png", "LICENSE"]:
        asset_path = os.path.join(SETUP_DIR, asset)
        if os.path.exists(asset_path):
            shutil.copy(asset_path, os.path.join(src_dir, asset))
            print(f"  Copied {asset}")

    # Run Python Sub-scripts
    py_exec = sys.executable 
    
    # 1. Generate Manifest
    subprocess.run([py_exec, os.path.join(SETUP_DIR, "generate_manifest.py"), toml_file, os.path.join(src_dir, "manifest.json")], check=True)
    
    # 2. Create Links
    link_src = os.path.join(PROFILE_PATH, "plugins", mod_name)
    link_data = os.path.join(PROFILE_PATH, "plugins_data", mod_name)
    subprocess.run([py_exec, os.path.join(SETUP_DIR, "create_links.py"), src_dir, data_dir, link_src, link_data], check=True)
    
    print("")
    return True

# --- 3.5 Set up Git Hooks ---
def configure_git_hooks():
    try:
        # Check if the .githooks folder exists in the root repo
        if os.path.exists(os.path.join(ROOT_DIR, ".githooks")):
            # Force the git command to execute in the ROOT_DIR, not the Setup dir
            subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=ROOT_DIR, check=True)
            print("  [DevOps] Local Git hooks configured successfully.")
    except Exception:
        print("  [DevOps] Warning: Could not configure git hooks automatically.")
        
# --- 4. Execution Loop ---
def main():
    configure_git_hooks()
    mod_count = 0
    
    # Gather directories to process (Searching from ROOT_DIR)
    targets = [
        os.path.join(ROOT_DIR, "adamant-modpack-Core"),
        os.path.join(ROOT_DIR, "adamant-modpack-Lib")
    ] + glob.glob(os.path.join(ROOT_DIR, "Submodules", "adamant-*"))
    
    for mod_dir in targets:
        if os.path.exists(os.path.join(mod_dir, "thunderstore.toml")):
            if setup_mod(mod_dir):
                mod_count += 1
                
    print("==========================================================")
    print(f"  Done. {mod_count} mods deployed.")
    print("==========================================================\n")

if __name__ == "__main__":
    main()