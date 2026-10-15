# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Naming note.** The project was originally scaffolded as **WinStitch Remake**
> (`winstitch-remake`, package `winstitch_remake`) and is now branded **mekstitch**
> (distribution `mekstitch`, package `src`). Entries below are grouped by the
> work that shipped, not by the name in use at the time; historical references to
> "WinStitch" describe the earlier name and the Ursa Software product this is a
> re-imagining of.

## [Unreleased]

### Added

- Documentation set: this `CHANGELOG.md` and a rewritten `README.md` describing
  the current package layout, the `Logic` / `ProjectLogic` contract, and the
  current feature set.
- `AGENTS.md` — contributor/agent guidance: repository layout, the layered
  architecture and data flow, coding conventions, the Fluent Widgets gotchas,
  the domain model, file formats and the headless verification workflow.
- `TUTORIAL.md` — end-user walkthrough: first chart, the drawing tools, zoom and
  view options, craft modes, gauge, the palette, image import, export,
  saving/undo, keyboard shortcuts, worked examples and troubleshooting.

### Changed

- **Rebrand to `mekstitch`.** The working directory, distribution name,
  application name, window title, organisation name, project file dialog
  filter, app icon asset and repository URLs all move from "WinStitch Remake"
  to "mekstitch". The package layout (`src.app`, `src.core`) is unchanged.
- **Simplified the app icon wiring.** `main.py` now loads the committed PNG
  directly with `window.setWindowIcon(QPixmap(Config.APP_ICON))`, with no
  `exists()` guard or string coercion.
- **Consolidated to a single virtualenv, `.venv`.** Both venvs carried the old
  `winstitch-remake` absolute path in their `activate` scripts, console-script
  shebangs and cached bytecode; these are rewritten to the new path and the
  redundant second venv (`.venv-fl`) is dropped.

### Removed

- `tools/make_icon.py` and the `tools/` directory. The icon generator was a
  one-off used to mint `src/assets/mekstitch.png`; the PNG is committed, so the
  script is dead weight.
- The `.venv-fl` virtualenv (and its `.gitignore` entry). A single `.venv`
  suffices; it already carried every dependency the app needs.

## [1.0.0] - 2026-10-14

Initial tracked release: a PySide6 rewrite of the previous Tauri 2 + React 19 +
Rust application, re-housed on the `momentum` project's package conventions.

### Added

#### Core (pure Python, `src/core/`)

- **Project model** (`model.py`) — `Project`, `YarnColor`, `Gauge`,
  `CraftMode` and the starter `default_palette()` (20 DMC-flavoured colours),
  plus `parse_hex` / `is_valid_hex` / `fmt_hex` helpers and `MODE_META` UI
  metadata. The `.wsjson` JSON shape stays compatible with the old Rust build
  (camelCase keys, `blockSize`, `stitchesPerUnit`).
- **Undo/redo history** (`history.py`) — a live `Project` plus snapshot-based
  undo/redo capped at 200 steps, with `mutate`, `replace`, `undo`, `redo` and
  `can_undo` / `can_redo` accessors.
- **Image import** (`images.py`) — resize an image onto the grid with a choice
  of resampling filter, optional Floyd–Steinberg dithering, transparency
  handling (transparent pixels become empty stitches), and median-cut
  quantisation to rebuild the palette from an image. Implemented on `QImage`,
  so there is no third-party imaging or numerics dependency.
- **Chart export** (`chart.py`) — `render_chart` produces a printable PNG with
  grid lines, heavier rules every N cells, C2C block outlines and matching
  symbol glyphs; `legend_text` emits a plain-text yarn list (colour, symbol,
  hex, stitch count). `ExportOptions` carries the rendering knobs.
- **Procedural symbols** (`glyphs.py`) — eight chart symbols drawn with
  `QPainter` rather than a font, so the on-screen chart and the exported PNG
  always agree on which symbol maps to which colour. Includes `contrast_for`
  for readable glyphs on any swatch and `draw_glyph` / `symbol_char`.
- **Project files** (`project_file.py`) — pretty-printed `.wsjson` save / load,
  guarded against truncated cell buffers on load; files written by the old Rust
  build load unchanged.
- **Session object** (`logic.py`) — a single `Logic` entry point owning the
  `History` (live project + undo) and the current file path, exposing
  `project`, `has_path()` and `suggested_name()`.
- **CRUD helpers** (`crud/project.py`) — `ProjectLogic`, a collection of small,
  UI-agnostic units of work that each return a `(ok, message)` tuple
  (`new_project`, `open_project`, `save_project`, `undo`, `redo`, `paint`,
  `flood_fill`, `set_name`, `set_mode`, `set_block_size`, `set_gauge`,
  `resize`, `add_color`, `update_color`, `remove_color`, `reset_palette`,
  `import_into_grid`, `build_palette_from_image`, `export_chart`,
  `export_legend`) so widgets never catch exceptions themselves.

#### GUI (`src/app/`)

- **Application window** (`app.py`) — a `FluentWindow` that owns the session
  handles (`logic`, `async_helper`), registers each page as a navigation
  sub-interface (Chart, Image, Export, and About in the bottom position),
  applies the theme + local stylesheet, installs the keyboard shortcuts, and
  exposes `projectChanged` / `notify_project_changed()` so pages stay in sync.
- **Chart editor page** (`pages/chart.py`) — toolbar (New / Open / Save /
  Save As, Undo / Redo, zoom), the painted canvas inside a Fluent scroll area,
  a right-hand column of labelled Fluent fields (project name, width, height;
  craft radios plus C2C block size; gauge stitches / rows / unit with a live
  finished-size hint; grid + symbol toggles; palette panel) and a bottom readout
  strip.
- **Image import page** (`pages/import_page.py`) — choose an image and either
  map it onto the grid or rebuild the palette, with resample filter, dithering
  and transparency options, all run off the GUI thread.
- **Export page** (`pages/export_page.py`) — chart PNG settings and yarn-list
  export.
- **About page** (`pages/about.py`) — version, stack and links.
- **Canvas** (`components/canvas.py`) — the custom-painted chart editor: zoom,
  and tools for pencil, eraser, flood fill, line, rectangle (hold `Shift` to
  fill) and an eyedropper; drags that leave the canvas still commit correctly.
  Emits `cellsCommitted`, `floodFillRequested`, `colorPicked` and `hovered`.
- **Reusable fields** (`components/fields.py`) — `Field`, `NumberField`,
  `FloatField`, `TextField`, `SelectField`, plus `hbox` / `switch_row` helpers.
  Fields keep a draft value while typing and commit on Enter / focus-out so a
  mutation never fires on every keystroke.
- **Palette panel** (`components/palette_panel.py`) — a swatch grid of custom
  `SwatchButton`s with stitch counts, a selected-colour editor (name, colour
  picker, hex) and add / update / remove / reset actions.
- **Tool rail** (`components/toolrail.py`) — the vertical tool picker.
- **Readout** (`components/readout.py`) — the bottom strip showing cursor
  position, finished size, colour counts and status messages.
- **New chart dialog** (`components/new_chart_dialog.py`) — Fluent
  `MessageBoxBase` dialog to pick size and craft mode.
- **Page base** (`components/base_page.py`) — `BasePage` holding `logic` /
  `async_helper` and providing `handle_error_success()` (Fluent `InfoBar`
  toasts) and `report()` for `(ok, message)` results.
- **Background work helpers** (`utils/`) — `AsyncHelper` (a thin `QThreadPool`
  wrapper for fire-and-forget work) and `AsyncWorker` (a `QRunnable` reporting
  `started` / `finished` / `error` / `progress` through Qt signals), so image
  import and export never block the GUI thread.

#### Project scaffolding

- `src/main.py` entry point (`mekstitch` console script -> `src.main:main`)
  that builds the `QApplication`, creates the `Logic` session, hands both to the
  `FluentWindow` and runs the event loop.
- `src/config.py` — a single `Config` class (paths + metadata) every other
  module imports instead of hard-coding filesystem paths.
- `src/assets/` — the local Fluent stylesheet (`styles.qss`) and the app icon.
- `pyproject.toml` — setuptools packaging with explicit `src` package discovery
  and package-data covering the stylesheet and assets.
- `README.md`, `.gitignore`, `.vscode/extensions.json`, `.env.example`.

### Changed

- **Re-housed the Tauri 2 + React 19 + Rust build as a PySide6 application.**
  The Rust core (`src-tauri/src/`) became `src/core/`; the React UI became
  `src/app/` (Qt widgets). The chart renderer, image import, model and project
  file formats were ported with their behaviour and file-compatibility intact.
- **Adopted the `momentum` package conventions** as the organising pattern:
  an entry point at `src/main.py`, a `Config`, a single `Logic` session object,
  per-entity CRUD classes under `core/crud/` returning `(ok, message)`
  results, one `QWidget` page per screen under `app/pages/`, reusable widgets
  under `app/components/`, shared async helpers under `app/utils/`, and Fluent
  `InfoBar` toasts for feedback instead of ad-hoc status dialogs.
- **Rebuilt the UI on Fluent Widgets** (`qfluentwidgets`): Fluent buttons,
  fields, switches, radio buttons, scroll areas and the `FluentWindow`
  navigation shell replace the previous bespoke widget layer.

### Fixed

- `SelectField` now passes `userData=` to Fluent's
  `ComboBox.addItem(text, icon, userData)`, so `value()` and `findData()` work
  and the gauge unit combo round-trips correctly.
- `PalettePanel` re-selects the colour it just appended, so the editor targets
  the new entry immediately after "Add".
- `HyperlinkButton` on the About page uses the positional `(url, text)`
  constructor, matching Fluent's `singledispatchmethod` signature.
- `Project.from_dict` pads or trims the cell buffer to `width * height`, so a
  corrupt or hand-edited file cannot produce an out-of-range grid.

### Removed

- The Tauri/Rust/React sources and the previous flat `src/app/` layout
  (`main_window.py`, `topbar.py`, `side_panel.py`, `statusbar.py`, `theme.py`,
  `widgets.py`) in favour of the package structure above.

[Unreleased]: https://github.com/mekasu0124/mekstitch/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/mekasu0124/mekstitch/releases/tag/v1.0.0
