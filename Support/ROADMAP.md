# Roadmap — Core as a Framework Library

## Goal

Extract the orchestration infrastructure (discovery, hash, UI, HUD) into a reusable framework that any future project can adopt without forking, without interference between projects running simultaneously, and without inheriting adamant-specific assumptions.

The motivation is not just "support two Hades 2 packs" — it is that the current infrastructure is well-designed and worth preserving as a foundation. Future projects should be able to stand it up with a thin coordinator and get everything for free.

## Context

Core is currently a singleton mod (`adamant-Modpack_Core`). It owns all orchestration logic directly. If a second modpack wanted the same infrastructure, it would need to fork Core — duplicating code that would drift over time.

The solution is to split Core into two layers:
- **Framework** — pure library, all the machinery, parameterized by pack identity
- **Coordinator** — thin mod per pack, calls Framework.init, owns nothing else

## Phase 1 — String convention for `modpackModule` ✅ DONE

**Why now:** This is a one-line change per module that unblocks everything later without breaking anything today.

Change every module's definition from:
```lua
modpackModule = true,
```
to:
```lua
modpack = "h2-modpack",
```

Change Core's discovery filter from:
```lua
if definition.modpack then
```
to:
```lua
if definition.modpack == Core._packId then
```

Where `Core._packId = "h2-modpack"` is set in Core's `main.lua`.

`"h2-modpack"` is still truthy — any code that checks `if definition.modpack then` without comparing still works. No existing module breaks.

**Files to update:**
- All 35+ `Submodules/adamant-*/src/main.lua` definitions
- `h2-modpack-template/src/main.lua` and `main_special.lua`
- `adamant-modpack-coordinator/src/discovery.lua` (filter condition)
- `adamant-modpack-coordinator/src/main.lua` (set `Core._packId`)
- `Support/CLAUDE.md` (update the "Adding a module" section)

---

## Phase 2 — Extract Framework library ✅ DONE

> **HUD stacking** — implemented as multiple separate `ScreenData.HUD.ComponentData` elements, each named `ModpackMark_<packId>`, offset by `packIndex * 24px`. Revisit for in-game validation once a second modpack is created and both packs run simultaneously.

## Phase 2 — Extract Framework library (detail)

### New component: `adamant-Modpack_Framework`

A library mod (like Lib), not a standalone mod. Accessed via `rom.mods['adamant-Modpack_Framework']`.

It exposes a single entry point:
```lua
local Framework = rom.mods['adamant-Modpack_Framework']
local pack = Framework.init({
    packId      = "adamant",
    windowTitle = "adamant modpack",
    config      = config,        -- the coordinator's own Chalk config (profiles, etc.)
})
-- pack.Discovery, pack.Hash, pack.HUD, pack.renderWindow(), pack.Theme
```

`Framework.init` is called once per coordinator. It returns a self-contained pack table with no global side effects. Two coordinators can call it with different `packId` values and get independent systems.

### What moves into Framework

Everything currently in `adamant-modpack-coordinator/src/`:
- `discovery.lua` — parameterized by `packId`
- `hash.lua` — pure logic, no changes needed
- `hud.lua` — parameterized (which HUD component to inject)
- `ui.lua` — parameterized (window title, pack identity)
- `ui_theme.lua` — shared as-is, or each pack can supply its own

### What stays in the coordinator (`adamant-Modpack_Core`)

```lua
-- main.lua — the entire coordinator
local Framework = rom.mods['adamant-Modpack_Framework']
local pack = Framework.init({ packId = "adamant", windowTitle = "adamant modpack", config = config })

rom.gui.add_imgui(function()
    pack.renderWindow()
end)
```

The coordinator becomes ~20 lines. All logic lives in Framework.

### Key design challenges

**1. Global namespace (`Core.X`)**
Currently all internal files share state via `Core.Discovery`, `Core.Theme`, `Core.Hash`. In Framework, these become fields on the `pack` table returned by `Framework.init`. Internal files use upvalues instead of globals.

**2. `import 'file.lua'` pattern**
The engine's `import` runs in the current mod's context and merges into shared globals. Framework files cannot use `import` to share state between themselves — they need explicit table passing or a module-level closure.

**3. UI is the largest file**
`ui.lua` references `Core.Discovery`, `Core.Theme`, `Core.Def` extensively. These become parameters to an `initUI(discovery, theme, def, config)` factory function that closes over them and returns `renderWindow`.

**4. HUD stacking**
`hud.lua` injects into `ScreenData.HUD.ComponentData`. Two problems arise when multiple packs run simultaneously:

- **Name collision**: both packs inject `ModpackMark`, second one overwrites the first. Fix: pack-scope the component name (`"ModpackMark_adamant-modpack"`).
- **Position collision**: two separately-named components at the same Y position render on top of each other, making both unreadable.

Solution — **self-registering offset**: `Framework.init` writes each pack's `packId` into a shared global table (`_G._FrameworkPacks = _G._FrameworkPacks or {}`). Each HUD component queries this table at render time to find its registration index, then applies `index * lineHeight` as a Y offset. No separate manager mod needed. Packs stack vertically in load order, each occupying its own line.

### Migration path

1. Create `adamant-Modpack_Framework` repo
2. Copy Core's src files into Framework, refactor globals → closure/upvalue pattern
3. Core becomes a coordinator (thin wrapper)
4. Verify Core + Framework produce identical behavior to current Core alone
5. Add Framework as a dependency in Core's `thunderstore.toml`
6. Any new pack creates its own coordinator, lists Framework as dependency

---

## Phase 3 — Multi-pack support (next)

Once Framework exists, a second modpack (e.g. `another-modpackcoordinator`) can use the same infrastructure:

```lua
-- another-modpackcoordinator/src/main.lua
local Framework = rom.mods['adamant-Modpack_Framework']
local pack = Framework.init({ packId = "another", windowTitle = "another modpack", config = config })
```

Modules in the second pack set `modpack = "another-modpack"` and are invisible to the adamant pack's discovery. Both packs run simultaneously with independent windows, hashes, and profiles.

---

## Decision log

- **Why not fork Core?** Code drift. Any fix or feature in Core infrastructure would need to be applied to both forks manually.
- **Why not two instances of the same Core mod?** The engine loads each mod ID once. Two coordinators with the same mod ID is not possible.
- **Why a library and not a shared base class?** Lua doesn't have inheritance. A factory function (`Framework.init`) returning a self-contained table is the idiomatic Lua equivalent and aligns with how Lib is already structured.
- **`modpackModule` as string vs table** — string is simpler and sufficient. A module belonging to two packs simultaneously is not a use case we anticipate; if it ever is, the filter can be updated to `type(v) == "table" and contains(v, packId)`.
