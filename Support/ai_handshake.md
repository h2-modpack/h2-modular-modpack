# AI Handshake — Context Transfer Document

Use this file to dump session state when approaching context limits.
Copy-paste the relevant sections below into your new session's first message.

---

## Instructions for Outgoing AI

When you are running low on context, fill in the sections below and tell the user to copy this into their next session.

---

## Session Snapshot

### Date
March 26, 2026

### What was being worked on

**Phase 2: complete.** Framework extraction done, Setup/ extracted to standalone submodule, all housekeeping verified. Next: create a second modpack (run-director) using `new_pack.py`.

### Key decisions made this session

1. **Framework extracted**: `discovery.lua`, `hash.lua`, `hud.lua`, `ui.lua`, `ui_theme.lua` all moved to `adamant-modpack-Framework/src/`. Each exposes one factory function on the `Framework` table. `Framework.init` wires them together.

2. **Public API pattern**: Framework uses `public.init = Framework.init` (not `public = Framework`) — ENVY holds a reference to the original `public` table, so reassignment doesn't work.

3. **GUI registration moved to coordinator**: Framework no longer calls `rom.gui.add_imgui` itself. It exposes `Framework.getRenderer(packId)` and `Framework.getMenuBar(packId)` — stable late-binding callbacks. The coordinator registers them once in `modutil.once_loaded.game`.

4. **Core renamed to coordinator**: GitHub repo `h2-modpack-Core` → `h2-modpack-coordinator`. Local folder `adamant-modpack-Core` → `adamant-modpack-coordinator`. Thunderstore mod identity (`adamant-Modpack_Core`) unchanged.

5. **Setup/ → own submodule (done)**: `Setup/` is now its own repo (`h2-modpack/Setup`), referenced as a submodule in shell repos. `new_pack.py` lives there and adds it as a submodule in new packs. README added.

6. **`new_pack.py`**: Scaffolds a new shell repo from scratch. Creates the coordinator GitHub repo via `gh repo create`, adds Lib and Framework as submodules, generates all coordinator files pre-filled, copies Setup/ scripts with a customized `deploy_common.py`. Usage: `python Setup/new_pack.py --output PATH --pack-id ID --title TITLE --namespace NS [--name Modpack_Core] [--org h2-modpack]`.

7. **Framework git history rewritten**: All commits rewritten to `maybe-adamant <maybe.adamant@gmail.com>` via `git filter-branch`.

8. **Framework registered as submodule** in shell repo (between Lib and Core in `.gitmodules`).

### Files modified this session

- `adamant-modpack-Framework/src/` — created: `main.lua`, `discovery.lua`, `hash.lua`, `hud.lua`, `ui.lua`, `ui_theme.lua`
- `adamant-modpack-Framework/src/main.lua` — `public.init`, `public.getRenderer`, `public.getMenuBar` exposed; `_registered` guard removed
- `adamant-modpack-coordinator/src/main.lua` — thin coordinator; registers GUI in `once_loaded.game`
- `adamant-modpack-coordinator/thunderstore.toml` — websiteUrl updated to `h2-modpack-coordinator`
- `adamant-modpack-coordinator/src/manifest.json` — website_url updated
- `.gitmodules` — Framework added; coordinator name/path fixed (`adamant-modpack-coordinator`)
- `Setup/deploy_common.py` — coordinator path updated to `adamant-modpack-coordinator`
- `Setup/new_pack.py` — created: full shell repo scaffolding script
- `adamant-modpack-Framework/.luacheckrc` — corrected globals for Framework
- `adamant-modpack-Framework/tests/` — moved from Core; TestHash uses `Framework.createHash` directly
- `adamant-modpack-Framework/.github/workflows/test.yaml` — created
- `adamant-modpack-Framework/.github/workflows/luacheck.yaml` — created
- `adamant-modpack-Framework/CONTRIBUTING.md` — full architecture doc for Framework

### Open issues / next steps

- **Create second modpack** (run-director) via `new_pack.py` — this is Phase 3 / the next step.
- **HUD stacking**: implemented as multiple `ScreenData.HUD.ComponentData` elements (`ModpackMark_<packId>`, `Y = 250 + (packIndex-1) * 24`). Needs in-game validation once two packs run simultaneously.
- **Framework not yet published to Thunderstore**: Version is `1.0.0`, CI in place, no release cut yet.
- **Update h2-modpack-template**: ✅ Done — `modpackModule = true` → `modpack = "h2-modpack"`, all "Core" references updated to "Framework"/"coordinator".
- **Group tiny modules by semantic function**: Some standalone modules are very small; consider merging related ones into slightly larger cohesive mods (e.g. grouped by game mechanic or category).

### Current state of the codebase

Phase 2 complete. Framework extracted and wired. Coordinator is 49 lines. Setup/ is a standalone submodule. Tests pass (23 in Framework). `release-all.yaml` already has `h2-modpack-coordinator` — no update needed. `new_pack.py` written but not yet run against a real second pack.

---

## Project Quick Reference

### Repo layout
- **Shell repo**: `h2-modular-modpack/` — git submodules
- **Coordinator** (`adamant-modpack-coordinator/`): thin pack coordinator (~50 lines), delegates to Framework
- **Framework** (`adamant-modpack-Framework/`): discovery, hash, HUD, UI — reusable across packs
- **Lib** (`adamant-modpack-Lib/`): shared utilities (backup, field types, state mgmt)
- **Modules** (`Submodules/adamant-*/`): 35 standalone mods, each its own repo
- **Setup/**: deployment + scaffolding scripts

### Tech stack
- Lua 5.1 (Hades 2 engine), 32-bit integers
- LuaUnit tests (Framework + Lib), Luacheck linting (all repos)
- Thunderstore packaging (tcli), r2modman mod manager
- GitHub Actions CI (luacheck, tests, release)

### Key files to read first
1. `Support/CLAUDE.md` — full project context
2. `adamant-modpack-Framework/CONTRIBUTING.md` — Framework architecture
3. `adamant-modpack-Lib/CONTRIBUTING.md` — Lib public API

### User preferences
- Pseudonym: "maybe-adamant" / org: "h2-modpack"
- Concise responses, no emoji unless asked
- Ask for feedback when a task feels complex or edge cases are consuming significant thought — don't investigate alone
- Prefers separate focused scripts over monoliths
