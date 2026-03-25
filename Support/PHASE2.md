# Phase 2 — Framework Extraction

## Goal

Extract Core's orchestration logic (discovery, hash, UI, HUD) into a reusable
`adamant-modpack-Framework` library mod. The coordinator (`adamant-modpack-coordinator`)
becomes a thin ~30-line wrapper that calls `Framework.init`. Any future pack
creates its own coordinator and gets everything for free.

---

## New repo: `adamant-modpack-Framework`

```
adamant-modpack-Framework/
  src/
    main.lua       — Framework table + Framework.init + imports sub-files
    discovery.lua  — createDiscovery(packId, lib)
    hash.lua       — createHash(discovery, lib)
    ui_theme.lua   — createTheme()
    hud.lua        — createHud(packId, packIndex, hash, theme, config, modutil)
    ui.lua         — createUI(discovery, hash, hud, theme, def, config, lib, windowTitle)
  thunderstore.toml
```

Same multi-file structure as current Core. Each file exposes a factory function
on the `Framework` table. `Framework.init` wires them together.

`lib` (`adamant-Modpack_Lib`) is NOT a param to `Framework.init` — Framework
fetches it itself from `rom.mods`. It is a fixed infrastructure dependency, not
a pack parameter.

---

## Framework.init signature

```lua
Framework.init({
    packId      = "h2-modpack",        -- discovery filter + HUD component name scoping
    windowTitle = "Speedrun Modpack",  -- UI window title
    config      = config,              -- coordinator's Chalk config (see contract below)
    def         = def,                 -- pack-specific data (see contract below)
    modutil     = modutil,             -- for hud.lua's Path.Wrap hook
})
```

### config contract

Framework expects the coordinator's `config` to have:
- `config.ModEnabled`  — bool
- `config.DebugMode`   — bool — **coordinator owns the framework debug gate**
- `config.Profiles`    — array of `{ Name, Hash, Tooltip }`

> **DebugMode decision (resolved):** `config.DebugMode` lives on the coordinator's config and gates
> `lib.warn(packId, config.DebugMode, msg)` calls throughout discovery, hash, and ui. This avoids
> the shared-state problem where multiple packs writing to `lib.config.DebugMode` would cause stale
> staging values in each other's Dev tabs. Each coordinator owns its own gate; Framework passes it
> through. `lib.config.DebugMode` is retained only for lib-internal diagnostics (`libWarn`), written
> by the "Lib Debug" checkbox in the Dev tab (direct read/write — intentional exception to staging,
> see ui.lua comment).

### def contract

```lua
def = {
    NUM_PROFILES    = #config.Profiles,
    defaultProfiles = {
        { Name = "...", Hash = "...", Tooltip = "..." },
        ...
    },
}
```

---

## Framework.init implementation

```lua
local _registered = {}   -- packId -> true  (GUI registration guard)
local _packs      = {}   -- packId -> { ui, hud, _index }  (late-binding for hot reload)
local _packList   = {}   -- ordered list of packIds for HUD Y-offset stacking

function Framework.init(params)
    local lib = rom.mods['adamant-Modpack_Lib']

    -- Self-register for HUD stacking (preserve index across reloads)
    local packIndex = _packs[params.packId] and _packs[params.packId]._index or nil
    if not packIndex then
        table.insert(_packList, params.packId)
        packIndex = #_packList
    end

    -- Create fresh subsystems each call (correct order matters)
    local discovery = Framework.createDiscovery(params.packId, lib)
    local hash      = Framework.createHash(discovery, lib)
    local theme     = Framework.createTheme()
    local hud       = Framework.createHud(params.packId, packIndex, hash, theme, params.config, params.modutil)
    local ui        = Framework.createUI(discovery, hash, hud, theme, params.def, params.config, lib, params.windowTitle)

    discovery.run()

    -- Store instances — overwrites on reload; GUI callbacks use late binding via _packs
    _packs[params.packId] = { ui = ui, hud = hud, _index = packIndex }

    -- Register GUI once per packId (guard against hot reload double-registration)
    if not _registered[params.packId] then
        _registered[params.packId] = true
        local packId = params.packId
        rom.gui.add_imgui(function()
            _packs[packId].ui.renderWindow()   -- late binding: picks up new instance after reload
        end)
        rom.gui.add_to_menu_bar(function()
            _packs[packId].ui.addMenuBar()
        end)
    end

    if params.config.ModEnabled then
        hud.setModMarker(true)
    end
end
```

**Hot reload correctness:** On reload `Framework.init` creates fresh instances and
updates `_packs[packId]`. The already-registered GUI callbacks pick up the new
instances via `_packs[packId].ui` / `.hud` — no double-registration, no stale state.

---

## Factory signatures and what changes in each file

### `createDiscovery(packId, lib)`
- Wrap existing body in factory function
- `Core._pack` → `packId`
- `Core.Discovery = Discovery` → `return Discovery`
- Everything else identical

### `createHash(discovery, lib)`
- Wrap in factory, close over `discovery`
- All `Core.Discovery.*` → `discovery.*` (~10 occurrences, mechanical)
- `Core.Hash = Hash` → `return Hash`
- Easiest refactor — file is already pure logic

### `createTheme()`
- No params
- Trivial: wrap body, `return Theme` instead of `Core.Theme = Theme`
- Future: could accept `overrides` table for pack-specific colors

### `createHud(packId, packIndex, hash, theme, config, modutil)`
- `Core.Hash` → `hash`
- `Core.Theme.colors.text` → `theme.colors.text`
- HUD component name: `"ModpackMark"` → `"ModpackMark_" .. packId`
- HUD component lookup: `HUDScreen.Components.ModpackMark` → `HUDScreen.Components["ModpackMark_" .. packId]`
- Y position: `Y = 250` → `Y = 250 + (packIndex - 1) * 24` (24px per pack line)
- Strip `Core.GetConfigHash`, `Core.ApplyConfigHash`, `Core.UpdateHash`, `Core.SetModMarker`
  — expose these on the returned table instead
- Returns `{ setModMarker, updateHash, getConfigHash, applyConfigHash }`

### `createUI(discovery, hash, hud, theme, def, config, lib, windowTitle)`
Mechanical substitutions:
- `Core.Discovery` → `discovery`
- `Core.Theme` → `theme`
- `Core.Def` → `def`
- `Core.GetConfigHash` → `hash.GetConfigHash`
- `Core.ApplyConfigHash` → `hash.ApplyConfigHash`
- `Core.UpdateHash()` → `hud.updateHash()`
- `Core.SetModMarker(val)` → `hud.setModMarker(val)`
- `"Speedrun Modpack"` (window title) → `windowTitle`
- Strip the `if not Core._uiRegistered then` guard block entirely —
  Framework.init owns registration now
- `lib.warn(msg)` → `lib.warn(packId, config.DebugMode, msg)` (already done in Core; same pattern in Framework)
- Returns `{ renderWindow, addMenuBar }`

**`SetupRunData`** — called in ui.lua as a bare global. It is a Hades 2 game
function. **Resolved:** Framework calls `import_as_fallback(rom.game)` itself at
the top of `Framework.init`, guaranteeing game globals are in scope for all
subsystem closures. The coordinator no longer needs to call it first.

**`lib.warn` signature (resolved, already implemented):** `lib.warn(packId, enabled, msg)`.
The coordinator's `config.DebugMode` is passed as `enabled` at every callsite in discovery,
hash, and ui. This mirrors `lib.log(name, enabled, msg)` — caller owns the gate.
Internal lib diagnostics use the private `libWarn(msg)` gated by `lib.config.DebugMode`.

---

## Coordinator after Phase 2

```lua
-- adamant-modpack-coordinator/src/main.lua  (~30 lines, no other src files)
local mods = rom.mods
mods['SGG_Modding-ENVY'].auto()

rom = rom ; _PLUGIN = _PLUGIN ; game = rom.game
modutil = mods['SGG_Modding-ModUtil']
chalk   = mods['SGG_Modding-Chalk']
reload  = mods['SGG_Modding-ReLoad']

config = chalk.auto('config.lua')
public.config = config

local Framework = mods['adamant-Modpack_Framework']

local def = {
    NUM_PROFILES    = #config.Profiles,
    defaultProfiles = {
        { Name = "AnyFear",  Hash = "1AfB0V.3", Tooltip = "RTA Disabled. Arachne Pity Disabled" },
        { Name = "HighFear", Hash = "1AfB0t.3", Tooltip = "RTA Disabled. Arachne Spawn Forced" },
        { Name = "RTA",      Hash = "1AfB20.3", Tooltip = "RTA Enabled. Arachne Pity Enabled." },
    },
}

local function init()
    import_as_fallback(rom.game)
    Framework.init({
        packId      = "h2-modpack",
        windowTitle = "Speedrun Modpack",
        config      = config,
        def         = def,
        modutil     = modutil,
    })
end

local loader = reload.auto_single()
modutil.once_loaded.game(function()
    loader.load(init, init)
end)
```

`def.lua` is eliminated — inlined directly into `main.lua`. No other src files remain in Core.

---

## Tests

hash.lua tests currently patch `Core.Discovery` as a global mock. After refactor,
pass a mock `discovery` table directly to `createHash(mockDiscovery, mockLib)`.
No global patching needed — cleaner.

---

## Migration steps (in order, each independently verifiable)

1. Create `adamant-modpack-Framework` repo, add `thunderstore.toml`
2. Copy Core's `src/` files into Framework as starting point
3. Refactor files in this order (least risky first):
   - `ui_theme.lua` → `createTheme()` (trivial, no deps)
   - `discovery.lua` → `createDiscovery(packId, lib)` (self-contained)
   - `hash.lua` → `createHash(discovery, lib)` (mechanical substitution)
   - `hud.lua` → `createHud(...)` (small file, add HUD stacking here)
   - `ui.lua` → `createUI(...)` (largest, but fully mechanical)
4. Write `Framework/src/main.lua` with `Framework.init`
5. Update Core: replace all `src/` with new `main.lua` (shown above),
   add Framework to `thunderstore.toml` dependencies
6. Update tests: pass mock `discovery` to `createHash` instead of patching `Core.Discovery`
7. Add Framework as submodule to shell repo
8. Update `release-all.yaml` — Framework is now in Submodules, auto-discovered

---

## Design decisions (resolved)

- [x] **`Framework.init` return value** — returns the `pack` table `{ discovery, hash, hud, ui }`
      so coordinators can access subsystems for debugging/extension at the module level.

- [x] **`import_as_fallback`** — Framework calls it itself at the top of `Framework.init`.
      Coordinator no longer responsible for this.

- [x] **HUD multi-pack stacking** — still open: single element with `\n` separator vs multiple
      screen elements. Both options remain viable; decision deferred until in-game testing.
      - Single `\n` element: engine handles line flow, no Y-offset math, simpler.
      - Multiple elements: each pack independently positioned, more control but needs pixel tuning.

- [x] **`config.DebugMode` ownership** — moved to coordinator config (already added to Core's
      `config.lua`). Each coordinator gates `lib.warn` with its own `config.DebugMode`.
      `lib.config.DebugMode` retained only for lib-internal `libWarn`. Dev tab has two separate
      checkboxes: "Framework Debug" → `config.DebugMode`, "Lib Debug" → `lib.config.DebugMode`.
      Both read/write directly (intentional exception to staging — no external writers).

- [x] **`lib.warn` signature** — **already implemented.** New signature: `lib.warn(packId, enabled, msg)`.
      All Core callsites updated. Private `libWarn(msg)` added for lib-internal use.
