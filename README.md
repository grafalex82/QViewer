# QViewer

QViewer is a lightweight, easy-to-use image viewer built with Python and
PyQt5. It is designed for quickly inspecting and reviewing images without leaving the
keyboard or returning to a file manager.

> **Inspiration:** QViewer is inspired by IrfanView, another lightweight and
> fast image viewer with an excellent user experience. Some QViewer hotkeys are
> therefore similar to IrfanView's. However, IrfanView lacks lasso zoom in
> full-screen mode, a capability QViewer provides. IrfanView is focused solely
> on viewing, so reviewing images requires a separate application. QViewer's
> review mode lets you select good images as you view them.

Main features are:
- Windowed and full-screen modes.
- Lasso or mouse-wheel zoom.
- Fast navigation between images in one folder and quick jumps between sibling folders.
- Review mode for marking good images and discarding the rest.

## Current status and roadmap

> **Work in progress:** QViewer is an active prototype. Some features are
> complete, while others are experimental or still planned.

The implemented behavior and known gaps are listed below.

- Viewer
  - [x] Open PNG and JPEG images from the File menu or the command line.
  - [ ] Support additional image formats (e.g. NEF, CR2).
  - [ ] Add a thumbnail browser or strip.
- View modes
  - [x] Windowed mode.
  - [x] Full-screen mode.
  - [x] Fit image to window.
  - [x] Show image at original (1:1) size.
  - [x] Rotate the current view left or right in 90-degree steps.
  - [ ] Add viewer preferences.
- Metadata
  - [x] Current file name in both windowed and full-screen mode
  - [x] Current file name index (e.g. image 5 of 10)
  - [x] Current-folder Keep and Reject counts alongside the file name
    (e.g. `[K:2 R:3]`; zero counts are omitted).
  - [ ] Show image metadata.
- Navigation
  - [x] Move to the previous or next file in the current directory.
  - [x] Jump to the first or last image in the current directory with `Home` or `End`.
  - [x] Move to the previous or next image marked Keep.
  - [x] Move to the previous or next sibling directory; the first image opens when the selected directory is not empty.
  - [ ] Remember recently opened files or folders.
  - [ ] Open images from ZIP archive like in normal directory.
- Zoom and pan
  - [x] Zoom in and out with keyboard shortcuts.
  - [x] Lasso zoom: drag a rectangle over the image, then click it to zoom.
  - [x] Unzoom with a Ctrl-mouse click
  - [x] Mouse-wheel zoom centred on the cursor.
  - [x] Pan a zoomed image with Shift-mouse drag.
- Review workflow
  - [x] Mark images as Keep or Reject.
  - [x] Discard unwanted images into a recoverable quarantine directory.
  - [x] Discard or permanently delete the current image after confirmation.

## Requirements

- Python 3.10 or newer
- PyQt5

## Setup

Create and activate a virtual environment, then install the project dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For a simple local setup, you can install the dependencies into your system
Python instead:

```powershell
python -m pip install -r requirements.txt
```

Using a virtual environment is still recommended to avoid dependency conflicts
with other Python projects.

## Run the viewer

Launch without an image and choose one with **File → Open**:

```powershell
python src/main.py
```

Or open an image directly:

```powershell
python src/main.py "C:\\Pictures\\example.jpg"
```

You can also open a folder; QViewer loads its first file alphabetically:

```powershell
python src/main.py "C:\\Pictures"
```

## Review workflow

Mark the current image as Keep or Reject while reviewing a directory. **Discard
Rejected** moves only images marked Reject and leaves both Keep and Undecided
images alone. **Keep Only Marked** is broader: it preserves only images marked
Keep, moving both Reject and Undecided images.

Both bulk operations process only supported image files directly inside the
current directory. They do not process images in child directories, sibling
directories, or unsupported files.

Discarding is recoverable. QViewer moves affected files, rather than permanently
deleting them, into a timestamped quarantine directory at
`<current directory>/.qviewer-discarded/<timestamp>/`. To recover an image, move
it from that timestamped directory back into the original directory. Press
`Delete` to discard only the current image. Press `Shift+Delete` to permanently
delete the current image from disk. Both actions ask for confirmation, remove
the image from the current file list, and advance to the next image.

## Controls

| Action | Shortcut |
| --- | --- |
| Open image | `Ctrl+O` |
| Quit | `Ctrl+Q` |
| Previous / next image | `Left` / `Right` or `Space` |
| Previous / next image marked Keep | `Shift+Left` / `Shift+Right` |
| First / last image | `Home` / `End` |
| Previous / next sibling folder | `Ctrl+Left` / `Ctrl+Right` |
| Toggle Keep | `K` |
| Toggle Reject | `X` |
| Keep and advance | `Ctrl+Up` |
| Reject and advance | `Ctrl+Down` |
| Discard current image | `Delete` |
| Permanently delete current image | `Shift+Delete` |
| Discard rejected images | `Ctrl+Delete` |
| Keep only marked images | `Ctrl+Shift+Delete` |
| Toggle full screen | `F` or `Enter` |
| Exit full screen, then quit | `Esc` |
| Zoom in / out | `+` / `-` |
| Rotate view left / right 90° | `L` / `R` |

Use the **View** menu to select fit-to-window or original-size display. To try
lasso zoom, drag a rectangle over the displayed image and click inside that
selection. Rotation affects only the current view: it does not modify the image
file or its Keep/Reject state, and it is discarded when you navigate away.

## Development

Run the test suite from the repository root:

```powershell
cd test
python -m pytest
```

The existing tests cover directory and file navigation. GUI interaction tests,
formatting, linting, and continuous integration are planned as part of the
developer-foundation work.

See the [test suite documentation](test/README.md) for test organization and
test creation guidelines.

## Project layout

```text
src/main.py                      Application entry point
src/main_window.py               Main window, menus, and shortcuts
src/image_view.py                Image display and zoom behavior
src/image_surface.py             Image painting and mouse selection
src/file_mgr.py                  Directory and image-navigation model
test/                            Automated tests
misc/                            Development image assets and helpers
```

## Contributing

Keep each change small and include tests whenever behavior changes. Before
opening a pull request, run the test command above and describe any manual GUI
checks performed.

## License

QViewer is free software licensed under the GNU General Public License,
version 3 or (at your option) any later version (`GPL-3.0-or-later`). See
[`LICENSE`](LICENSE) for the complete terms.

QViewer uses the GPL edition of PyQt5. If you distribute QViewer, including a
packaged executable, you must comply with the GPL and provide recipients with
the corresponding source code. Dependencies retain their own licenses; see
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
