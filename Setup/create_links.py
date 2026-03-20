import sys
import os

def create_directory_symlink(target_folder, link_path):
    """
    Creates a platform-aware symbolic link for a directory.

    On Windows, this requires Admin privileges.
    """

    # --- Step 1: Resolve to absolute paths ---
    # This makes the links robust, so they work regardless of where
    # the script is run from.
    try:
        abs_target = os.path.abspath(target_folder)
        abs_link = os.path.abspath(link_path)
    except Exception as e:
        print(f"Error resolving paths: {e}")
        return

    print(f"Attempting to link:\n  Target: {abs_target}\n  At:     {abs_link}")

    # --- Step 2: Check if target exists ---
    if not os.path.isdir(abs_target):
        print(f"Error: Target directory '{abs_target}' does not exist.")
        print("Skipping link creation.")
        return # This will stop the function from proceeding

    # --- Step 3: Check if link path is clear ---
    if os.path.exists(abs_link) or os.path.lexists(abs_link):
        print(f"Error: A file or link already exists at '{abs_link}'. Please remove it first.")
        return

    # --- Step 4: Create the link ---
    try:
        # os.symlink is the key function.
        # On Windows, 'target_is_directory=True' is necessary to
        # create a directory link (equiv. of 'mklink /D').
        # This argument is ignored on Unix-like systems.
        os.symlink(abs_target, abs_link, target_is_directory=True)
        print("...Success!")

    except OSError as e:
        # This is the most common error on Windows.
        if os.name == 'nt' and "A required privilege is not held by the client" in str(e):
            print("\n--- PERMISSION ERROR ---")
            print("On Windows, this script must be run as an Administrator to create symbolic links.")
            print("Please right-click your terminal (Command Prompt/PowerShell) and select 'Run as Administrator'.")
        else:
            print(f"\n...Error creating link: {e}")
    except Exception as e:
        print(f"\n...An unexpected error occurred: {e}")

# --- Main Script Execution ---
if __name__ == "__main__":
    # --- Step 0: Validate arguments ---
    if len(sys.argv) != 5:
        print("Usage: python create_links.py <folder1> <folder2> <link_path1> <link_path2>")
        print("\nExample (Unix/macOS):")
        print("  python3 create_links.py ./data/images ./data/docs /var/www/images /var/www/docs")
        print("\nExample (Windows):")
        print(r'  python create_links.py C:\MyData C:\MyLogs D:\Web\Data D:\Web\Logs')
        sys.exit(1)

    # Assign arguments to clear variable names
    folder1 = sys.argv[1]
    folder2 = sys.argv[2]
    link_path1 = sys.argv[3]
    link_path2 = sys.argv[4]

    print("--- Creating first link ---")
    create_directory_symlink(folder1, link_path1)

    print("\n--- Creating second link ---")
    create_directory_symlink(folder2, link_path2)

    print("\nScript finished.")
