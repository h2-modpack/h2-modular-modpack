# AI Handshake — Context Transfer Document

Use this file to dump session state when approaching context limits.
Copy-paste the relevant sections below into your new session's first message.

---

## Instructions for Outgoing AI

When you are running low on context, fill in the sections below and tell the user to copy this into their next session.

---

## Session Snapshot

### Date
March 24, 2026

### What was being worked on
Completed a full architectural audit of Core, Lib, Template, Setup scripts, and GitHub Actions CI/CD workflows. Applied major ImGui performance optimizations and fully decoupled the release orchestrator.

### Key decisions made this session
1. **Render Loop Purity:** Eliminated GC pressure by caching strings (`_pushId`), closures (`_onChangedCb`), and tables (`cachedTabList`) during Discovery/Init instead of in ImGui render loops.
2. **Dynamic Architecture over Hardcoding:** Reverted `BUG_FIX_CATEGORY` global constant to maintain the completely decoupled category discovery system.
3. **Template Extraction:** Fully moved templates into the standalone `h2-modpack-template` repo to keep the Lib package clean.
4. **Lockstep Versioning:** Decided to stick with lockstep versioning for mass releases. Updated `release-all.yaml` to dynamically auto-discover submodules (removing the need for `discovery_registry.lua`). Added bash guardrails requiring mass releases to end in `.0` and hotfixes to end in `>0` to prevent Thunderstore collisions.

### Files modified this session
- `Core/src/ui.lua` & `discovery.lua` - Applied GC allocation fixes (caching tables, closures, and ImGui IDs).
- `Template/src/main.lua` & `main_special.lua` - Added missing `modpackModule = true` and fixed ImGui ID window desync (`###`).
- `Setup/deploy_links.py` - Fixed a Windows-specific `PermissionError` when overwriting directory symlinks (`os.rmdir`).
- `.github/workflows/release-all.yaml` - Switched to auto-discovery of the `Submodules/` directory and added patch version guardrails.
- `.github/workflows/test.yaml` (Core/Lib) - Switched to `luarocks install luaunit` to prevent rolling master breaks.
- `.github/workflows/luacheck.yaml` (Lib) - Standardized file extension from `.yml`.

*(Note: `discovery_registry.lua` and `project-auto-add.yml` were marked for deletion).*

### Open issues / blockers
None. The architectural foundation is incredibly solid, tested, and optimized.

### Current state of the codebase
Highly optimized. Zero GC pressure in the main UI render loop. CI/CD is fully dynamic and decoupled. Tests are passing with 100% functional coverage of non-UI logic. Ready for standard module development.

---

## Project Quick Reference

### Repo layout
- **Shell repo**: `h2-modular-modpack/` — git submodules for 37 mods
- **Core** (`adamant-modpack-Core/`): discovery, unified UI, config hash, HUD
- **Lib** (`adamant-modpack-Lib/`): shared utilities (backup, field types, state management)
- **Modules** (`Submodules/adamant-*/`): 35 standalone mods, each its own repo
- **Setup/**: deployment scripts (`deploy_all.py`, `deploy_links.py`, etc.)
- **Template**: `h2-modpack-template/` (sibling directory) — GitHub template for new modules

### Tech stack
- Lua 5.1 (Hades 2 engine), 32-bit integers
- LuaUnit tests (Core + Lib), Luacheck linting (all repos)
- Thunderstore packaging (tcli), r2modman mod manager
- GitHub Actions CI (luacheck, tests, release)

### Key files to read first
1. `Support/CLAUDE.md` — full project context for AI assistants
2. `adamant-modpack-Lib/CONTRIBUTING.md` — Lib's public API and module contract
3. `adamant-modpack-Core/CONTRIBUTING.md` — Core architecture and discovery system

### User preferences
- Pseudonym: "maybe-adamant" / org: "h2-modpack"
- Concise responses, no emoji unless asked
- Prefers separate focused scripts over monoliths (deploy_links vs deploy_all)
- Lua 5.2 std in luacheck is intentional (manually verified compatible)
- Template repo is a sibling directory, not inside the shell repo
