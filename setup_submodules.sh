#!/bin/bash

# 1. Tell the shell repo's .gitmodules file that every submodule should track 'main'
echo "Configuring all submodules to track 'main'..."
git submodule foreach --quiet 'git config -f $toplevel/.gitmodules submodule.$name.branch main'

# 2. Update the submodules based on the new remote branch configuration
echo "Pulling latest updates for all submodules..."
git submodule update --remote --merge

# 3. Physically check out 'main' inside every submodule directory so you aren't in detached HEAD
echo "Checking out 'main' branch in all submodules..."
git submodule foreach --quiet 'git checkout main'

echo "=================================================="
echo "Done! All submodules are updated and on the 'main' branch."
echo "Note: If you haven't already, remember to commit the updated .gitmodules file to your shell repo!"
