# Adamant Modpack — Architecture Overview

## What this system is

The adamant modpack is a collection of independent game-modifying modules unified by a single UI and configuration system. Each module lives in its own repository and can be installed standalone, but when `adamant-Modpack_Core` is present it discovers all installed modules automatically, hosts them in a shared window, and manages their configuration as a single shareable hash.

The design goal is zero coupling between modules: a module author writes their logic, declares a definition table, and the rest is handled for them.

---

## Components

### `adamant-Modpack_Core`
The orchestrator. It owns:
- **Discovery** — scans loaded mods at startup for `modpack = "modpack-namespace"`
- **UI** — renders the shared window (sidebar, per-module tabs, quick setup, profiles, dev)
- **Hash/profiles** — encodes all module state into a portable string; manages named profile slots
- **HUD** — injects the fingerprint overlay into the game's HUD

Core has no knowledge of any specific module's internals. It communicates through the module contract (see below).

### `adamant-Modpack_Lib`
Shared infrastructure, accessed by every module as `rom.mods['adamant-Modpack_Lib']`. It provides:
- `createBackupSystem()` — deep-copy backup and restore of game data tables
- `createSpecialState()` — builds a staging table + snapshot/sync functions from a stateSchema
- `isEnabled(config)` — checks a module's own `Enabled` flag AND the master toggle when Core is present
- `warn(msg)` — framework diagnostic, gated on `lib.config.DebugMode`
- `log(name, enabled, msg)` — per-module trace, gated on the caller's own `config.DebugMode`
- `validateSchema(schema, label)` — checks a stateSchema at declaration time, warns on bad fields
- `drawField(ui, field, value, width)` — renders a widget for a given field descriptor type

Lib has no knowledge of Core. Any module can use it whether or not Core is installed.

### Individual modules
Each module is its own mod package. It declares a `definition` table and implements logic. It depends on Lib but is otherwise self-contained. Core discovers it; modules do not register themselves with Core.

### External dependencies
- **Chalk** — config file persistence (`config.lua` per mod). Slow I/O, not used in the render loop.
- **ENVY** — wires engine globals (`rom`, `public`, `_PLUGIN`) into the mod's scope.
- **ModUtil** — function wrapping (`Path.Wrap`) for hooking game functions.
- **ReLoad** — hot reload support (`auto_single()`).

---

## Module lifecycle

```
Game starts
  └─ each module file loads
       ├─ wires globals via ENVY
       ├─ declares public.definition
       ├─ builds stateSchema (special modules)
       └─ schedules modutil.once_loaded.game(...)

Game data loads
  ├─ Core runs discovery (scans rom.mods for modpack = "modpack-namespace")
  └─ each module's loader fires:
       ├─ import_as_fallback(rom.game)   ← makes game globals available
       ├─ registerHooks()                ← wraps game functions via ModUtil
       └─ if enabled: apply()            ← mutates game data / sets initial state

Player is in game
  ├─ hooks fire on game events (SetTraitsOnLoot, StartNewRun, etc.)
  └─ Core renders its UI window each frame:
       ├─ reads staging (plain Lua table — fast)
       ├─ calls module.DrawTab / DrawQuickContent for special modules
       └─ on user interaction → onChanged() → SyncToConfig() → Chalk write

Hash / profiles
  ├─ Core computes hash from all current configs
  └─ HUD fingerprint updates on room transition
```

---

## Regular modules vs special modules

### Regular module
A module that has a simple on/off state and optional inline options (dropdowns, checkboxes). Core renders its row in the module list and optionally an options panel. The module author only writes game logic.

Config shape: `config.Enabled` plus flat option keys (`config.Mode`, `config.Strict`, etc.).

### Special module
A module with complex, structured configuration that deserves its own sidebar tab. It owns its own UI entirely and declares a `stateSchema` so Core can hash its state.

Config shape: `config.Enabled` plus arbitrarily nested data (e.g. `config.FirstHammers.WeaponAxe`).

**Use a special module when:**
- The configuration is a structured data set, not a flat list of toggles
- The module benefits from a dedicated tab with custom layout
- You need nested config keys in the hash

---

## The staging pattern

Chalk reads and writes config files on disk. That I/O is acceptable at load time or on explicit user action, but not in a 60 fps render loop.

Every module that has UI keeps a **staging table** — a plain Lua table that mirrors the Chalk config. The render loop reads and writes staging exclusively. Chalk is only touched in two controlled moments:

- **`SnapshotStaging()`** — re-reads Chalk into staging. Called at init, after a profile load, and after hot reload.
- **`SyncToConfig()`** — flushes staging into Chalk. Called by `onChanged()` after any user interaction that modifies state.

For special modules, `lib.createSpecialState(config, stateSchema)` builds the staging table and returns both functions automatically.

---

## The hash and profile pipeline

### Canonical string (the shareable hash)
Core walks all discovered modules and specials and collects every value that differs from its declared default:

```
_v=1|ModId=1|ModId.OptionKey=value|adamant-SpecialMod.configKey=value
```

- `ModId=1` / `ModId=0` — module enabled state (omitted if at default)
- `ModId.OptionKey=value` — inline option value (omitted if at default)
- `adamant-SpecialMod.configKey=value` — special module field (omitted if at default)
- Keys are sorted alphabetically for stable output
- All-defaults produces `_v=1` (version token only)

The format is key-value, not positional. Adding or removing modules does not corrupt existing hashes.

### Fingerprint
A dual-pass djb2 checksum of the canonical string, base62-encoded to a fixed 12-character string. Displayed in the HUD as a visual confirmation that two setups match. Not decodable — it is only used for at-a-glance comparison.

### Applying a hash
`ApplyConfigHash` parses the canonical string. For each module/field: if a key is present in the hash, apply that value; if absent, reset to the declared default. Unknown keys are ignored (forward compatibility). The version token `_v` must be present or the hash is rejected.

### Profiles
Named slots (stored in Core's own config) each containing a canonical hash string, a display name, and a tooltip. Saving captures the current hash. Loading calls `ApplyConfigHash` then re-snapshots all staging tables.

---

## The theme contract

Core passes a `theme` table to `DrawTab(ui, onChanged, theme)` and `DrawQuickContent(ui, onChanged, theme)`. This table contains:

- `theme.colors` — the full color palette (`info`, `success`, `error`, `warning`, `text`, `textDisabled`, and all widget background colors)
- `theme.FIELD_MEDIUM / FIELD_NARROW / FIELD_WIDE` — layout proportions as fraction of window width
- `theme.ImGuiTreeNodeFlags` — flag constants (`DefaultOpen`, `Leaf`, `Framed`, `CollapsingHeader`, ...)
- `theme.PushTheme() / PopTheme()` — apply or remove the full color theme (useful for standalone windows)

Theme does **not** provide text-color helper functions. Modules call ImGui directly:

```lua
-- Colored text
ui.TextColored(r, g, b, a, text)

-- Disabled/hint text (auto-uses ImGuiCol.TextDisabled, themed by PushTheme)
ui.TextDisabled(text)

-- Scoped header text color (tight push/pop = zero blast radius)
local headerColor = (colors and colors.info) or {1, 1, 1, 1}
ui.PushStyleColor(ImGuiCol.Text, table.unpack(headerColor))
local open = ui.CollapsingHeader("Section")
ui.PopStyleColor()
```

Label column offset (where the input widget starts after a label) is **not** in theme — it is module-specific because it depends on the length of the module's label text. Each module declares its own `DEFAULT_LABEL_OFFSET`.

---

## File map

```
adamant-Modpack_Core/
  src/
    main.lua          — entry point, wires Core table, imports all src files
    discovery.lua     — scans rom.mods, builds Discovery (modules, specials, categories)
    hash.lua          — GetConfigHash / ApplyConfigHash / EncodeBase62 / DecodeBase62
    hud.lua           — injects mod marker component, updates fingerprint display
    ui.lua            — full ImGui window: sidebar, tabs, profiles, dev panel
    ui_theme.lua      — color palette, layout constants, PushTheme/PopTheme
  tests/
    all.lua           — test runner
    TestUtils.lua     — engine mock, MockDiscovery factory
    TestHash.lua      — hash encoding/decoding/round-trip tests

adamant-Modpack_Lib/
  src/
    main.lua          — all lib utilities (one file, accessed as a mod)
  tests/
    all.lua           — test runner
    TestUtils.lua     — engine mock, lib loader
    Test*.lua         — per-feature test suites

adamant-FirstHammer/  (example special module)
  src/
    main.lua          — definition, data tables, hooks, DrawTab, DrawQuickContent
  config.lua          — default config (Chalk reads this)

h2-modpack-template/
  src/
    main.lua          — regular module template
    main_special.lua  — special module template
```
