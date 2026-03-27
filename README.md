# h2-modular-modpack

Reference shell repo for the h2-modpack architecture. Demonstrates how Lib, Framework, a coordinator, and standalone module submodules wire together.

## Structure

```
h2-modular-modpack/
├── adamant-ModpackShowcaseCore/   # Coordinator: pack identity, config, profiles
├── adamant-ModpackFramework/      # Shared UI, discovery, hash, HUD
├── adamant-ModpackLib/            # Shared utilities
├── Setup/                         # Deploy scripts
└── Submodules/                    # Game modules (one repo each)
```

## Setup

```bash
git clone --recurse-submodules https://github.com/h2-modpack/h2-modular-modpack.git
python Setup/deploy/deploy_all.py
```

Requires Python 3 and r2modman with a profile named `h2-dev`. On Windows, run `Setup/win.bat` as Administrator. On Linux/macOS, run `sudo ./Setup/lin.sh`.

## Starting a new pack

See [Setup/README.md](Setup/README.md) for scaffolding a new pack from scratch.

## Architecture

- [adamant-ModpackFramework](https://github.com/h2-modpack/ModpackFramework) — full architecture docs
- [adamant-ModpackLib](https://github.com/h2-modpack/ModpackLib) — shared utilities API
- [h2-modpack-template](https://github.com/h2-modpack/h2-modpack-template) — starting point for new modules
