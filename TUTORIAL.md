# mekstitch — Tutorial

A hands-on walkthrough of mekstitch, from an empty grid to a printed chart.
If you just want the feature list, see the [README](README.md); this document
takes you through using it.

- [1. Install and launch](#1-install-and-launch)
- [2. The window at a glance](#2-the-window-at-a-glance)
- [3. Your first chart](#3-your-first-chart)
- [4. Drawing tools](#4-drawing-tools)
- [5. Zoom and view options](#5-zoom-and-view-options)
- [6. Craft modes](#6-craft-modes)
- [7. Gauge and finished size](#7-gauge-and-finished-size)
- [8. The palette](#8-the-palette)
- [9. Importing an image](#9-importing-an-image)
- [10. Exporting](#10-exporting)
- [11. Saving, opening, undo/redo](#11-saving-opening-undoredo)
- [12. Keyboard shortcuts](#12-keyboard-shortcuts)
- [13. Worked examples](#13-worked-examples)
- [14. Troubleshooting](#14-troubleshooting)

---

## 1. Install and launch

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

Then start the app:

```bash
mekstitch
```

If you'd rather not install the console script:

```bash
python -m src.main
```

The first launch opens with a **60 × 60 cross-stitch chart** and a 20-colour
starter palette, ready to draw.

---

## 2. The window at a glance

mekstitch is a single window with a left navigation rail and four pages.

| Page | What it's for |
|---|---|
| **Chart** | The editor — draw stitches, set project properties, edit the palette |
| **Image** | Turn a photo into stitches, or build a palette from one |
| **Export** | Render a printable PNG and a plain-text yarn list |
| **About** | Version and stack info (bottom of the rail) |

The **Chart** page is where you'll spend most of your time. It has four regions:

```
┌──────────────────────────────────────────────────────────────┐
│ toolbar: New Open Save SaveAs │ Undo Redo │ −  14px  + │ Title │
├────┬──────────────────────────────────────────┬──────────────┤
│    │                                          │ Project      │
│ T  │                                          │ Craft        │
│ o  │            the canvas                    │ Gauge        │
│ o  │       (the stitch grid)                  │ View         │
│ l  │                                          │ Palette      │
│ s  │                                          │              │
├────┴──────────────────────────────────────────┴──────────────┤
│ readout: size · colours · finished size · zoom · cursor      │
└──────────────────────────────────────────────────────────────┘
```

- **Toolbar** — file actions, undo/redo, zoom, and the chart title.
- **Tool rail** (far left) — the six drawing tools.
- **Canvas** (centre) — the grid. Scroll it with the scrollbars; it stays
  centred while it fits.
- **Right column** — Project, Craft, Gauge, View and Palette panels, top to
  bottom, in a scroll area.
- **Readout** (bottom) — live stats: grid size, colour/block count, finished
  size, zoom, cursor cell, and the colour you're currently painting with.

---

## 3. Your first chart

Let's make a small heart on a 20 × 20 grid.

1. **New chart.** Click **New** in the toolbar (or press <kbd>Ctrl</kbd>+<kbd>N</kbd>).
   In the dialog, set **Width** `20`, **Height** `20`, **Craft**
   `Cross Stitch`, then click **Create**.
2. **Pick a colour.** In the right column, the **Palette** panel shows colour
   swatches. Click the red swatch (`666 Red`). The editor above it now targets
   that colour, and the readout chip updates to show it.
3. **Draw.** The **Pencil** tool is already selected. Click and drag on the
   canvas to paint red stitches. Because this is a drag, you can sketch the
   whole outline in one motion — the stroke commits when you release the mouse.
4. **Fix mistakes.** Switch to the **Eraser** tool (second button in the rail)
   and drag over stitches to clear them back to empty.
5. **Fill a block.** Select the **Rectangle** tool, drag from one corner to the
   other, and hold <kbd>Shift</kbd> while dragging to fill the block instead of
   just outlining it. Release to commit.
6. **Check your work.** Give the chart a name in **Project → Name** (type it and
   press <kbd>Enter</kbd>). The title in the toolbar updates to match.

That's the loop: pick a tool, pick a colour, draw. Everything you draw is one
undo step.

---

## 4. Drawing tools

The tool rail runs top to bottom:

| Tool | Icon | What it does |
|---|---|---|
| **Pencil** | pen | Paints single stitches; drag to paint a freehand stroke |
| **Eraser** | eraser | Clears stitches to empty; drag to erase a stroke |
| **Fill** | paint-bucket | Flood-fills the connected region of the same colour under the cursor |
| **Line** | diagonal | Drag from A to B; commits a straight Bresenham line on release |
| **Rectangle** | square | Drag from A to B; outlines a rectangle — hold <kbd>Shift</kbd> to fill it |
| **Eyedropper** | palette | Click a stitch to make its colour the active one |

Notes:

- **Drags that leave the canvas still commit.** You can start a stroke on the
  grid, drag off the edge, and come back — nothing is lost.
- The **Line** and **Rectangle** tools show a live preview while you drag and
  only commit on release, so the whole shape is a single undo step.
- The **Eyedropper** sets the active palette colour from whatever cell you
  click; it's the fastest way to match an existing colour.

---

## 5. Zoom and view options

Use the **−** / **+** buttons in the toolbar to change zoom (2–64 px per cell;
default 14). The current zoom shows next to the buttons and in the readout as
`14px/cell`.

Under **View** in the right column:

- **Grid lines** — show/hide the cell grid (on by default).
- **Symbols** — overlay the chart symbol for each colour (off by default). Turn
  this on to see what the printed chart will look like, where symbols do the
  work of distinguishing similar colours.

In **Corner-to-Corner** mode the grid also draws **block outlines** every
`block_size` cells, so you can see the C2C blocks.

---

## 6. Craft modes

The same grid is reinterpreted per craft. Set the mode with the radio buttons
under **Craft**:

| Mode | How one unit maps |
|---|---|
| **Cross Stitch** | 1 cell = 1 cross stitch |
| **Crochet (Single)** | 1 cell = 1 single crochet |
| **Corner-to-Corner** | 1 block = 1 C2C pixel; block size is adjustable |
| **Tunisian Simple Stitch** | 1 cell = 1 TSS |
| **Knitting** | 1 cell = 1 knit stitch (colourwork) |

When you pick **Corner-to-Corner**, a **Block size** field appears (default 5).
1 cell on the design still maps to 1 painted cell, but the finished-size maths
and the block outlines both use this size — so a 5×5 block of cells becomes one
C2C pixel.

Changing the mode never alters the stitches; it only changes how they're
counted and displayed. The readout swaps "colours" for "blocks" in C2C mode.

---

## 7. Gauge and finished size

**Gauge** tells mekstitch how big a finished stitch is, so it can report the
finished dimensions of the piece.

- **Stitches** — stitches per unit (default 4.5)
- **Rows** — rows per unit (default 5.5)
- **Unit** — `Inches` or `Centimetres`

Edit any of them and the **readout** and the hint under the Gauge section
update immediately, e.g. `Finished ≈ 4.4 × 3.6 in`. C2C accounts for the block
size automatically. Changing the gauge doesn't change the chart — only the
reported measurement.

---

## 8. The palette

The **Palette** panel manages the colours your chart can use.

**Select a colour** by clicking its swatch. The active colour gets a ring and
drives the Pencil / Line / Rectangle tools; the readout chip shows it too.

**Edit the selected colour:**

- **Name** — a display name (`666 Red`, `Sky`, whatever you like).
- **Colour** — click the picker swatch to open the Fluent colour dialog, or
  type a hex value (`#RRGGBB`) in the field next to it.
- **Update** — apply the name/hex to the selected swatch.
- **Remove** — delete the colour. Any stitches using it are cleared, and later
  palette indices are remapped so the rest of the chart stays correct.
  (You can't remove the last remaining colour.)
- **Reset** — restore the 20-colour starter palette.

**Add a colour:** in the **New** row at the bottom, type a name, pick a colour,
and click **Add**. The new swatch is appended and selected automatically, so you
can start using it right away.

Each swatch tooltip shows the colour name, hex, and how many stitches use it.

### Symbols

Every palette index has a **chart symbol** (there are eight, cycling by index).
Symbols are drawn procedurally — not with a font — so the on-screen chart and
the exported PNG always agree on which symbol belongs to which colour. Turn on
**View → Symbols** to see them on the canvas, and see
[Exporting](#10-exporting) for how they appear in print.

---

## 9. Importing an image

The **Image** page turns a photo into stitches. There are two independent
routes.

### Route A — map the photo onto the current palette

Use this when you already have your colours and want the photo fitted onto
them.

1. Click **Choose image** and pick a file (PNG, JPG, GIF, BMP, WebP, TIFF).
2. Set **Width** / **Height** — the grid the image is resized onto.
3. Choose a **Resample** filter:

   | Filter | Best for |
   |---|---|
   | Nearest (pixel art) | Pixel art and clean edges — no blurring |
   | Triangle | A good general default |
   | Catmull-Rom | Smoother, slightly sharper than Triangle |
   | Lanczos3 | Sharpest; best for photographic sources |

4. Toggle **Floyd–Steinberg dithering** (on by default) — trades smooth
   gradients for a stippled look that reads better in a limited palette. Turn it
   off for flat regions.
5. Toggle **Transparent pixels become empty stitches** (on by default) — where
   the source is transparent, the grid is left empty.
6. Click **Import into grid**. The work runs off the UI thread, so the window
   stays responsive; the buttons disable until it finishes.

The imported result **replaces** the grid and takes on the width/height you set.

### Route B — build a palette from the photo

Use this when you want the photo's own colours.

1. Choose the image (same picker as above).
2. Under **Build palette from image**, set **Colours** (2–256; default 24).
3. Click **Build palette**.

mekstitch quantises the image with median-cut, replaces your palette with the
resulting colours, and remaps the grid to them. The new palette then shows up on
the Chart page, ready to edit like any other.

---

## 10. Exporting

The **Export** page renders your chart for printing and for your project bag.

| Setting | Meaning |
|---|---|
| **Cell size (px)** | Pixel size of each cell in the PNG (4–64; default 16) |
| **Major line every** | Draw a heavier rule every N cells (0 = none; default 10) |
| **Grid lines** | Include the light cell grid |
| **Symbols** | Include the chart symbol in each coloured cell |

A **live preview** shows exactly what you'll get (it's disabled for very large
charts to keep things quick).

Two export buttons:

- **Export PNG chart** — writes a printable PNG. You'll be prompted for a
  location; the suggested filename is your chart name plus `.png`.
- **Export yarn list** — writes a plain-text list of every colour as
  name, symbol, hex and stitch count — the shopping list for your project.

Both report success or failure with a toast in the corner.

---

## 11. Saving, opening, undo/redo

Charts are saved as **`.wsjson`** — pretty-printed JSON that also loads files
from the original Rust build of this app.

| Action | How |
|---|---|
| New | **New** button / <kbd>Ctrl</kbd>+<kbd>N</kbd> |
| Open | **Open** button / <kbd>Ctrl</kbd>+<kbd>O</kbd> |
| Save | **Save** button / <kbd>Ctrl</kbd>+<kbd>S</kbd> (prompts on first save) |
| Save As | **Save As** button |
| Undo | **Undo** button / <kbd>Ctrl</kbd>+<kbd>Z</kbd> |
| Redo | **Redo** button / <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd> (or <kbd>Ctrl</kbd>+<kbd>Y</kbd>) |

**Undo/redo is snapshot-based** and holds the last **200 steps**. Every
committed operation — a pencil stroke, a fill, a resize, a palette edit — is one
step. Opening or creating a chart starts a fresh history.

The **Undo** and **Redo** toolbar buttons grey out when there's nothing left to
do, so you always know where you are.

---

## 12. Keyboard shortcuts

| Shortcut | Action |
|---|---|
| <kbd>Ctrl</kbd>+<kbd>N</kbd> | New chart |
| <kbd>Ctrl</kbd>+<kbd>O</kbd> | Open chart |
| <kbd>Ctrl</kbd>+<kbd>S</kbd> | Save |
| <kbd>Ctrl</kbd>+<kbd>Z</kbd> | Undo |
| <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd> / <kbd>Ctrl</kbd>+<kbd>Y</kbd> | Redo |
| <kbd>Shift</kbd> (hold) | Fill instead of outline, with the Rectangle tool |
| <kbd>Enter</kbd> | Commit a text/number field (fields don't save as you type) |

---

## 13. Worked examples

### A C2C blanket square

1. **New** → 50 × 50. Craft: **Corner-to-Corner**, block size 5 (default).
2. On the Chart page the grid shows block outlines every 5 cells. The readout
   now reports `10 × 10 blocks (5×5)`.
3. Use **Fill** to lay down a background colour, then **Pencil**/**Rectangle**
   for the motif.
4. Set **Gauge** to your C2C pixel gauge (e.g. 4 pixels per inch) and read the
   finished size from the readout.
5. **Export → Export PNG chart** for a printable chart, and **Export yarn list**
   for the colours.

### A photo turned into cross stitch

1. **New** → size it to your fabric count, Craft: **Cross Stitch**.
2. Go to the **Image** page, choose your photo, set the width/height to the
   grid you want, pick **Lanczos3**, leave dithering **on**.
3. Click **Import into grid**, then return to **Chart** to review.
4. Prefer a cleaner palette? Go back and use **Build palette from image** with
   `16` colours instead, then touch up with the Pencil and Eyedropper.

### Knitting colourwork

1. **New** → Craft: **Knitting**.
2. Set **Gauge** to your knitting gauge (stitches and rows per inch differ, so
   the finished size reflects the non-square cells).
3. Draw the motif; put **Symbols** on while you work so you can tell similar
   shades apart, then export a chart with symbols for reference while knitting.

---

## 14. Troubleshooting

**My colour change didn't apply.** Name and hex edits commit when you click
**Update** (or press <kbd>Enter</kbd>), not as you type. That's deliberate, so a
half-typed hex value never corrupts the palette.

**A field is ignoring my edits.** Fields keep your in-progress typing and won't
be overwritten by the app while focused. Click away or press <kbd>Enter</kbd> to
commit.

**Removing a colour changed my chart.** That's expected: stitches using the
removed colour are cleared, and later colours are re-indexed so the rest of the
chart stays correct. Undo (<kbd>Ctrl</kbd>+<kbd>Z</kbd>) reverses it.

**The import is slow.** Large photos are quantised and resampled; the work
happens off the UI thread so the window stays usable. The export preview is
disabled above ~250,000 cells on purpose.

**The whole grid looks like one symbol.** Symbols cycle through eight variants
by palette index, so on a palette with many colours some will share a symbol
shape until you trim the palette.

**It won't open my old file.** mekstitch reads `.wsjson` (and `.json`) written
by the original Rust build. If a file has a truncated cell buffer it's padded
or trimmed on load rather than rejected, but a malformed JSON file will fail
with a clear error toast.

---

## Where files live

- **Charts** — wherever you save them, as `.wsjson`.
- **Exports** — PNG charts and text yarn lists, wherever you save them.
- **Stylesheet and icon** — `src/assets/` (development only).

See [AGENTS.md](AGENTS.md) for the code architecture, and
[CHANGELOG.md](CHANGELOG.md) for what changed when.
