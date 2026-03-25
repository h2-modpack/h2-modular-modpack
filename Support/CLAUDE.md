# Adamant Modpack — AI Assistant Context

## Project Structure

This is a **Hades 2 modular modpack** organized as a shell repo with 37 git submodules under the `h2-modpack` GitHub org.

```
h2-modular-modpack/           # Shell repo
├── adamant-modpack-Core/      # Orchestrator: discovery, UI, hash, HUD
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
├── h2-modpack-template/       # Module templates (main.lua, main_special.lua)
├── Support/
│   ├── CLAUDE.md              # This file
│   └── ROADMAP.md             # Future architecture plans
├── ARCHITECTURE.md            # Full system bird's-eye overview (read this first)
└── .github/workflows/
    ├── release-all.yaml       # Orchestrates releases across all repos
    └── update-submodules.yaml # Daily submodule pointer sync
```

## Architecture

See `ARCHITECTURE.md` at the repo root for the full system overview including module lifecycle, staging pattern, hash pipeline, and theme contract.

### Module System
- Each module is a standalone Thunderstore mod with its own `thunderstore.toml`, `src/main.lua`, and `config.lua`
- Modules declare a `public.definition` table (id, name, category, group, options, apply/revert)
- `def.category` is a human-readable tab label string (e.g. `"Bug Fixes"`, `"Run Modifiers"`, `"QoL"`) — used as both lookup key and display label
- Core is an **orchestrator**: it discovers modules, sequences their lifecycle, hosts their UI, and aggregates their state. Modules have zero knowledge of Core or each other.
- Lib provides: `createBackupSystem()`, `createSpecialState()`, `standaloneUI()`, field type registry (toHash/fromHash/draw/validate), path helpers
- Modules work standalone (own ImGui window) or coordinated (Core handles UI)

### Module Types
- **Regular module**: flat `config.Enabled` + optional inline options. Core renders a row + options panel.
- **Special module**: `special = true`, own sidebar tab, `stateSchema` for Core hashing, `staging` table for fast UI reads. Implements `DrawTab(ui, onChanged, theme)` and `DrawQuickContent(ui, onChanged, theme)`.

### Key Technical Details
- **Lua 5.1** runtime (Hades 2's engine), 32-bit integers only
- **Config hash**: key-value canonical string (`_v=1|ModId=1|ModId.configKey=val|adamant-Special.key=val`), only non-default values encoded. `_v` version key must be present or hash is rejected. 12-char base62 fingerprint shown on HUD (dual-seed djb2, not decodable). Import/export uses canonical string.
- **Backup system**: first-call-only semantics, backup() saves original, revert() restores
- **Staging pattern**: plain Lua tables mirror Chalk config. UI reads/writes staging only. `SyncToConfig()` flushes to Chalk on user interaction. `SnapshotStaging()` re-reads from Chalk at init/reload/profile load.
- **ModifyTextBox({ Text = "" })** does NOT clear text — must use `ClearText = true`

### Theme Contract (Core.Theme)
Passed to special module `DrawTab` / `DrawQuickContent` as the `theme` parameter. Contains **data only** — no helper functions.

- `theme.colors` — full color palette (`info`, `success`, `error`, `warning`, `text`, `textDisabled`, all widget bg colors)
- `theme.FIELD_MEDIUM / FIELD_NARROW / FIELD_WIDE` — input field width as fraction of window width
- `theme.ImGuiTreeNodeFlags` — full flag table (`None`, `DefaultOpen`, `Leaf`, `Framed`, `CollapsingHeader`, ...)
- `theme.PushTheme() / PopTheme()` — apply/remove full color theme (useful for standalone module windows)

Theme does **not** provide text-color helpers. Modules call ImGui directly:
```lua
ui.TextColored(r, g, b, a, text)           -- colored text (unpack color table)
ui.TextDisabled(text)                       -- auto-uses ImGuiCol.TextDisabled
-- CollapsingHeader text color (tight scope = zero blast radius):
local headerColor = (colors and colors.info) or {1, 1, 1, 1}
ui.PushStyleColor(ImGuiCol.Text, table.unpack(headerColor))
local open = ui.CollapsingHeader("Section")
ui.PopStyleColor()
```

`LABEL_OFFSET` (where the input widget starts after a label) is **not** in theme — it is module-specific. Each module declares its own `DEFAULT_LABEL_OFFSET`.

### File Patterns
- `src/main.lua` — module entry point (ENVY auto, chalk config, modutil hooks)
- `src/config.lua` — default config values (Chalk persists user changes)
- `thunderstore.toml` — package metadata (namespace, name, version, dependencies)
- `Setup/` — per-repo local dev: `init_repo.bat/.sh` (hooks + branch protection), `deploy_local.bat/.sh` (assets + manifest + symlinks)
- `.luacheckrc` — per-repo luacheck config with module-specific globals
- `.lua-format` — LuaFormatter config (column_limit: 120)

## Testing
- Tests use **LuaUnit** on **Lua 5.1** (`C:\libs\lua51\lua.exe` on this machine)
- Core tests: `adamant-modpack-Core/tests/` — key-value hash round-trips, omit-defaults, fingerprint stability, error handling
- Lib tests: `adamant-modpack-Lib/tests/` — field types, path helpers, validation, backup, state mgmt
- Engine globals are mocked in `TestUtils.lua` (rom, ENVY, chalk, modutil, **Chalk mock required for lib load**)
- Run tests: `cd <repo> && lua5.1 tests/all.lua`

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
- Canonical templates in `h2-modpack-template/src/` (`main.lua`, `main_special.lua`)

### Adding a module to discovery
- Set `modpackModule = true` in the module's `public.definition` — Core auto-discovers it on load
- Set `def.category` to the desired tab name (e.g. `"Bug Fixes"`) — new tabs are created automatically
- No registry file, no Core PR, no CI enforcement needed
