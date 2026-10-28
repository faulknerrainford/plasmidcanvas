Installation
============

PlasmidEasel runs on Windows, macOS and Linux. You can either download a
standalone executable or run it from source.

Option 1: Standalone executable
-------------------------------

No Python installation is needed.

1. Open the project's `Releases page <https://github.com/faulknerrainford/plasmidcanvas/releases>`_.
2. Download the file for your system: ``PlasmidEasel-windows.exe``,
   ``PlasmidEasel-macos`` or ``PlasmidEasel-linux``.
3. On macOS and Linux, make the file executable: ``chmod +x PlasmidEasel-<system>``.
4. Run it.

.. note::
   The executables are unsigned. Windows SmartScreen or macOS Gatekeeper may
   warn you the first time you run the app. On Windows choose
   *More info → Run anyway*. On macOS right-click the file, choose *Open*,
   then confirm.

Option 2: Run from source
-------------------------

Requirements
~~~~~~~~~~~~

* Python 3.10 or higher
* Tcl/Tk (``tkinter``), which is not installed by ``pip``:

  * **Windows:** included with the python.org installer (keep
    "tcl/tk and IDLE" ticked).
  * **macOS:** included with the python.org installer. With Homebrew Python
    run ``brew install python-tk@3.x`` (matching your Python version).
  * **Linux:** Debian/Ubuntu ``sudo apt install python3-tk``; Fedora
    ``sudo dnf install python3-tkinter``; Arch ``sudo pacman -S tk``.

  Check Tk works with ``python -m tkinter``, which should open a small test
  window.

Steps
~~~~~

.. code-block:: bash

   git clone https://github.com/faulknerrainford/plasmidcanvas.git
   cd plasmidcanvas
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install matplotlib ttkbootstrap pandas biopython
   cd src
   python -m plasmideasel.PlasmidEasel

Alternatively, install the dependencies with `Poetry <https://python-poetry.org>`_
by running ``poetry install`` in the project root.

Troubleshooting
---------------

``ModuleNotFoundError: No module named 'tkinter'``
   Tk is missing. Install it as described above.

The window does not open on Linux
   A graphical display is required (X11, or Wayland with XWayland).
