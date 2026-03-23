#!/bin/bash
# Post-clone initialization for adamant-* submodule repos.
# Run once after creating a new repo from the template.

set -e

echo "Initializing repo DevOps..."

# 1. Configure git to use the committed hooks directory
if [ -d ".githooks" ]; then
    git config core.hooksPath .githooks
    echo "Git hooks configured (.githooks/)."
else
    echo "Warning: .githooks/ directory not found. Skipping hook setup."
fi

# 2. Lock the main branch via GitHub CLI
if command -v gh &> /dev/null; then
    echo "Setting up branch protection on main..."
    gh api -X PUT "repos/{owner}/{repo}/branches/main/protection" --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["lint"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0
  },
  "restrictions": null
}
EOF
    echo "Branch protection enabled."
else
    echo "Warning: gh CLI not found. Set up branch protection manually."
fi

echo "Done."
