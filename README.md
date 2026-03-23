# H2 modpack

Modular modpack for Hades II. Each module is a standalone mod that works independently or together through a shared coordinator (Core).

## Repository structure

```
adamant-modpack-Core/    -- coordinator: unified UI, profiles, config hashing
adamant-modpack-Lib/     -- shared library: module contract, field types, utilities
Submodules/              -- all individual modules
Setup/                   -- local deployment scripts
```

## Prerequisites

- [r2modman](https://thunderstore.io/package/ebkr/r2modman/) (or r2modmanPlus) with a profile named `h2-dev`
- Python 3
- Administrator privileges (Windows) or root (Linux/macOS) for symlink creation

## Local setup

1. Clone the repo with submodules:

```
git clone --recurse-submodules https://github.com/h2-modpack/h2-modular-modpack.git
```

2. Run the setup script for your platform:

**Windows** — right-click `Setup/win.bat` and select "Run as administrator"

**Linux/macOS** — `sudo ./Setup/lin.sh`

The script will, for each module:
- Copy `icon.png` and `LICENSE` into the module's `src/` folder
- Generate `manifest.json` from `thunderstore.toml`
- Symlink `src/` and `data/` into the r2modman dev profile

3. Launch Hades II through r2modman using the `h2-dev` profile.

## Contributing

See [Core CONTRIBUTING.md](https://github.com/h2-modpack/h2-modpack-Core/blob/main/CONTRIBUTING.md) and [Lib CONTRIBUTING.md](https://github.com/h2-modpack/h2-modpack-Lib/blob/main/CONTRIBUTING.md).
