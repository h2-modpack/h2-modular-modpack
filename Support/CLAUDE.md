# Adamant Modpack — AI Assistant Context

## Project Structure

This is a **Hades 2 modular modpack** organized as a shell repo with 37 git submodules under the `h2-modpack` GitHub org.

```
h2-modular-modpack/           # Shell repo
├── adamant-modpack-Core/      # Coordinator: discovery, UI, hash, HUD
├── adamant-modpack-Lib/       # Shared library: backup, field types, state mgmt
├── Submodules/
│   └── adamant-*/             # 35 standalone modules (each is its own repo)
├── Setup/                     # Deployment scripts (deploy_*, archive/)
│   ├── deploy_all.py          # Full deploy orchestrator
│   ├── deploy_links.py        # Symlinks only
│   ├── deploy_manifests.py    # Manifest generation only
│   ├── deploy_assets.py       # Icon + LICENSE copy only
│   ├── deploy_hooks.py        # Git hooks config only
│   └── deploy_common.py       # Shared utilities (mod discovery, args)
└── .github/workflows/
    ├── release-all.yaml       # Orchestrates releases across all repos
    └── update-submodules.yaml # Daily submodule pointer sync
```

## Architecture

### Module System
- Each module is a standalone Thunderstore mod with its own `thunderstore.toml`, `src/main.lua`, and `config.lua`
- Modules declare a `public.definition` table (id, name, category, group, options, apply/revert)
- Lib provides: `createBackupSystem()`, `createSpecialState()`, `standaloneUI()`, field encode/decode, path helpers
- Core discovers installed `adamant-*` modules via `rom.mods`, provides unified UI and config hashing
- Modules work standalone (own ImGui toggle) or coordinated (Core handles UI)

### Key Technical Details
- **Lua 5.1** runtime (Hades 2's engine), 32-bit integers only
- **Config hash**: base62 encoding, 30-bit chunks (CHUNK_BITS=30), format `<bool_hash>.<option_hash>`
- **Backup system**: first-call-only semantics, backup() saves original, revert() restores
- **Special modules**: have `stateSchema` for Core hashing, `staging` table for fast UI reads
- **ModifyTextBox({ Text = "" })** does NOT clear text — must use `ClearText = true`

### File Patterns
- `src/main.lua` — module entry point (ENVY auto, chalk config, modutil hooks)
- `src/config.lua` — default config values (Chalk persists user changes)
- `thunderstore.toml` — package metadata (namespace, name, version, dependencies)
- `Setup/` — per-repo local dev: `init_repo.bat/.sh` (hooks + branch protection), `deploy_local.bat/.sh` (assets + manifest + symlinks)
- `.luacheckrc` — per-repo luacheck config with module-specific globals

## Testing
- Tests use **LuaUnit** on **Lua 5.1** (`C:\libs\lua51\lua.exe` on this machine)
- Core tests: `adamant-modpack-Core/tests/` — hash encode/decode, chunk boundaries, round-trips
- Lib tests: `adamant-modpack-Lib/tests/` — field types, path helpers, validation, backup, state mgmt
- Engine globals are mocked in `TestUtils.lua` (rom, ENVY, chalk, modutil)
- Run tests: `cd <repo> && lua tests/all.lua`

## CI/CD
- **Luacheck** on all 37 repos (push/PR to main)
- **LuaUnit tests** on Core and Lib (push/PR to main)
- **Branch protection** on Core and Lib (require CI pass)
- **Release**: per-repo `release.yaml` (workflow_dispatch), shell repo `release-all.yaml` orchestrates
- **Submodule sync**: daily midnight UTC cron updates submodule pointers

## Deploy Scripts (Setup/)
All deploy_* scripts accept `--overwrite` (default: skip existing) and `--profile NAME` (default: h2-dev).

```bash
python Setup/deploy_all.py                    # full deploy
python Setup/deploy_links.py                  # symlinks only
python Setup/deploy_manifests.py --overwrite  # regenerate all manifests
python Setup/deploy_hooks.py                  # configure git hooks
```

## Common Tasks

### Adding a new module
1. Create repo from `h2-modpack-template` on GitHub
2. Run `Setup/init_repo.sh` (Linux) or `Setup/init_repo.bat` (Windows) to configure hooks + branch protection
3. Copy `src/main.lua` (standard) or `src/main_special.lua` (special module)
4. Fill in `public.definition`, `apply()`, `registerHooks()`
5. Update `thunderstore.toml` with actual name/description
6. Add as submodule to shell repo

### Modifying hash logic
- Pure logic in `Core/src/hash.lua` (no engine deps)
- Tests in `Core/tests/TestHash.lua`
- HUD rendering in `Core/src/hud.lua` (uses `Core.Hash`)

### Modifying Lib API
- Source in `Lib/src/main.lua`
- Tests in `Lib/tests/` (TestFieldTypes, TestPathHelpers, TestValidation, etc.)
- Template files in `Lib/src/template.lua` and `Lib/src/special_template.lua`
