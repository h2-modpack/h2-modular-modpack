# Adamant Modpack — AI Assistant Context

## Project Structure

This is a **Hades 2 modular modpack** organized as a shell repo with git submodules under the `h2-modpack` GitHub org.

```
h2-modular-modpack/               # Shell repo
├── adamant-modpack-coordinator/  # Thin coordinator: packId, config, def (~50 lines)
├── adamant-modpack-Framework/    # Reusable library: discovery, hash, HUD, UI
├── adamant-modpack-Lib/          # Shared utilities: backup, field types, state mgmt
├── Submodules/
│   └── adamant-*/                # 35 standalone modules (each is its own repo)
├── Setup/                        # Standalone submodule (h2-modpack/Setup)
│   ├── deploy_all.py             # Full deploy orchestrator
│   ├── deploy_links.py           # Symlinks only
│   ├── deploy_manifests.py       # Manifest generation only
│   ├── deploy_assets.py          # Icon + LICENSE copy only
│   ├── deploy_hooks.py           # Git hooks config only
│   ├── deploy_common.py          # Shared utilities (mod discovery, args)
│   ├── commit_submodules.py      # Commit + push all Submodules/* with shared message
│   ├── generate_manifest.py      # Single-mod manifest generation
│   └── new_pack.py               # Scaffold a new shell repo (gh + git submodules)
├── Support/
│   ├── CLAUDE.md                 # This file
│   └── ROADMAP.md                # Future architecture plans
├── ARCHITECTURE.md               # Full system overview
└── .github/workflows/
    ├── release-all.yaml          # Orchestrates releases across all repos
    └── update-submodules.yaml    # Daily submodule pointer sync
```

## Architecture

See `ARCHITECTURE.md` for the full system overview.

### Layer overview

| Layer | Repo | Role |
|---|---|---|
| Coordinator | `adamant-modpack-coordinator` | Owns: packId, windowTitle, defaultProfiles, config.lua. Delegates everything else to Framework. |
| Framework | `adamant-modpack-Framework` | Reusable library: discovery, hash, HUD, UI. Exposes `Framework.init(params)`. |
| Lib | `adamant-modpack-Lib` | Shared utilities used by Framework and standalone modules. |
| Modules | `Submodules/adamant-*` | Standalone mods. Opt into the pack via `public.definition.modpack = packId`. |

### Framework (adamant-modpack-Framework)

Coordinator calls `Framework.init(params)` and gets everything for free. Sub-files:

```
src/
  main.lua        -- Framework table, ENVY wiring, Framework.init, public API
  discovery.lua   -- createDiscovery(packId, config, lib)
  hash.lua        -- createHash(discovery, config, lib, packId)
  ui_theme.lua    -- createTheme()
  hud.lua         -- createHud(packId, packIndex, hash, theme, config, modutil)
  ui.lua          -- createUI(discovery, hud, theme, def, config, lib, packId, windowTitle)
```

Public API on `public`:
- `public.init(params)` — initialize or reinitialize a coordinator
- `public.getRenderer(packId)` — returns stable late-binding imgui callback
- `public.getMenuBar(packId)` — returns stable late-binding menu bar callback

**Critical**: Framework uses `public.init = Framework.init` (not `public = Framework`). ENVY holds a reference to the original `public` table — reassigning the variable doesn't work.

**GUI registration is the coordinator's responsibility**. Framework never calls `rom.gui.add_imgui` directly. The coordinator registers once in `modutil.once_loaded.game`:
```lua
rom.gui.add_imgui(Framework.getRenderer(PACK_ID))
rom.gui.add_to_menu_bar(Framework.getMenuBar(PACK_ID))
```

### Coordinator (adamant-modpack-coordinator)

~50 lines. Owns only: `packId`, `windowTitle`, `defaultProfiles`, `config.lua` schema. Everything else is Framework's responsibility. GitHub repo: `h2-modpack/h2-modpack-coordinator`. Thunderstore identity: `adamant-Modpack_Core` (unchanged for backwards compatibility).

### Module System
- Each module is a standalone Thunderstore mod with its own `thunderstore.toml`, `src/main.lua`, and `config.lua`
- Modules declare a `public.definition` table (id, name, category, group, options, apply/revert)
- `def.category` is a human-readable tab label string (e.g. `"Bug Fixes"`, `"Run Modifiers"`, `"QoL"`)
- Modules opt into a pack via `public.definition.modpack = packId` — no registry needed
- Modules work standalone (own ImGui window) or coordinated (Framework handles UI)

### Module Types
- **Regular module**: flat `config.Enabled` + optional inline options
- **Special module**: `special = true`, own sidebar tab, `stateSchema` for hashing, `staging` table

### Key Technical Details
- **Lua 5.1** runtime (Hades 2's engine), 32-bit integers only
- **Config hash**: key-value canonical string (`_v=1|ModId=1|ModId.configKey=val`), only non-default values encoded. 12-char base62 fingerprint shown on HUD.
- **Backup system**: first-call-only semantics
- **Staging pattern**: plain Lua tables mirror Chalk config. UI reads/writes staging only.
- **`public = Framework` does NOT work** — use `public.init = Framework.init` etc.

### Theme Contract
Passed to special module `DrawTab` / `DrawQuickContent` as the `theme` parameter.
- `theme.colors` — full color palette
- `theme.FIELD_MEDIUM / FIELD_NARROW / FIELD_WIDE` — input field width fractions
- `theme.ImGuiTreeNodeFlags` — full flag table
- `theme.PushTheme() / PopTheme()` — apply/remove full color theme

## Testing
- Tests use **LuaUnit** on **Lua 5.1** (`lua5.1` on Linux, `C:\libs\lua51\lua.exe` on Windows)
- Framework tests: `adamant-modpack-Framework/tests/` — hash round-trips, fingerprint stability
- Lib tests: `adamant-modpack-Lib/tests/` — field types, path helpers, backup, state mgmt
- Run: `cd <repo> && lua5.1 tests/all.lua`

## CI/CD
- **Luacheck** on all repos (push/PR to main)
- **LuaUnit tests** on Framework and Lib (push/PR to main)
- **Release**: per-repo `release.yaml`, shell repo `release-all.yaml` orchestrates all
- **Submodule sync**: daily midnight UTC cron

## Deploy Scripts (Setup/)

`Setup/` is a standalone submodule (`h2-modpack/Setup`). All deploy_* scripts accept `--overwrite` and `--profile NAME` (default: h2-dev).

```bash
python Setup/deploy_all.py                    # full deploy (assets + manifests + symlinks + hooks)
python Setup/deploy_links.py                  # symlinks only
python Setup/deploy_manifests.py --overwrite  # regenerate all manifests
python Setup/deploy_hooks.py                  # configure git hooks
python Setup/commit_submodules.py "msg"       # commit + push all Submodules/* with shared message
```

### Scaffolding a new pack

Clone Setup standalone, run `new_pack.py`, then discard the clone (it re-enters as a submodule):

```bash
git clone https://github.com/h2-modpack/Setup
python Setup/new_pack.py \
  --pack-id "my-pack" \
  --namespace mynamespace \
  [--title "My Pack"] \
  [--name Modpack_Core] \
  [--org h2-modpack]
cd ../my-pack-modpack
python Setup/deploy_all.py
```

Creates GitHub coordinator repo via `gh`, adds Lib/Framework/Setup as submodules, generates all coordinator files pre-filled.

## Common Tasks

### Adding a new module
1. Create repo from `h2-modpack-template` on GitHub
2. Set `public.definition.modpack = "h2-modpack"` and fill in `def.category`, `apply()`, `revert()`
3. Add as submodule: `git submodule add --branch main <url> Submodules/<name>`
4. Run `python Setup/deploy_all.py --overwrite`

### Modifying hash logic
- Pure logic in `adamant-modpack-Framework/src/hash.lua` (no engine deps)
- Tests in `adamant-modpack-Framework/tests/TestHash.lua`

### Modifying Lib API
- Source in `adamant-modpack-Lib/src/main.lua`
- Tests in `adamant-modpack-Lib/tests/`
