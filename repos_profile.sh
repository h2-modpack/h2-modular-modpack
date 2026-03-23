#!/bin/bash

# Removed -type d so it finds both standard repos (.git folder) and submodules (.git file)
find . -name ".git" -prune | while read -r gitpath; do
    # Extract the repository path
    repo_dir=$(dirname "$gitpath")
    echo "Applying anonymous profile to: $repo_dir"
    
    # Apply configurations using the -C flag to target the specific directory
    git -C "$repo_dir" config --local user.name "maybe-adamant"
    git -C "$repo_dir" config --local user.email "maybe.adamant@gmail.com"
    git -C "$repo_dir" config --local core.sshCommand "ssh -i ~/.ssh/id_ed25519_anon -o IdentitiesOnly=yes"
done

echo "Profile update complete."
