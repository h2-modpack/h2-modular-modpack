# AI Handshake — Context Transfer Document

Use this file to dump session state when approaching context limits.
Copy-paste the relevant sections below into your new session's first message.

---

## Instructions for Outgoing AI

When you are running low on context, fill in the sections below and tell the user to copy this into their next session.

---

## Session Snapshot

### Date
<!-- Fill: today's date -->

### What was being worked on
<!-- Fill: the current task, what's done, what remains -->

### Key decisions made this session
<!-- Fill: any architectural choices, user preferences, or approaches agreed upon -->

### Files modified this session
<!-- Fill: list of files changed with one-line descriptions -->

### Open issues / blockers
<!-- Fill: anything unresolved that the next session needs to handle -->

### Current state of the codebase
<!-- Fill: any important state that isn't obvious from reading the code
     (e.g., "tests are passing", "deploy scripts untested", "branch X has uncommitted changes") -->

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
