Saving Output
=============

PlasmidEasel can save two things: the **map image** (for figures and
publications) and the **feature data** (so you can reopen and keep editing
later).

Saving the map image
--------------------

1. Choose **File → Save As...**.
2. Pick a location and type a file name **including the extension**
   (for example ``pBR322.png``).
3. Choose the file type from the dialog's type list.

.. list-table::
   :header-rows: 1
   :widths: 15 15 70

   * - Format
     - Extension
     - Best for
   * - PNG
     - ``.png``
     - Slides, web pages and general use (raster image).
   * - SVG
     - ``.svg``
     - Editing in vector tools such as Inkscape or Illustrator, and scalable
       figures.
   * - PDF
     - ``.pdf``
     - Publications and printing (vector image).
   * - JPG
     - ``.jpg``
     - Small files where transparency is not needed (raster image).

.. note::
   The format is taken from the extension in the file name, so always type it.
   The map is saved as currently displayed, cropped tightly around the plasmid.

Saving the feature data
-----------------------

Use the **Save Data** button in the **Table** tab to save the feature table
and reopen it in a later session.

1. Click **Save Data**. If the table is empty a warning is shown instead.
2. Choose the format when asked: **Yes** saves a CSV (comma-separated) and
   **No** saves a TSV (tab-separated).
3. Choose a file name and location.

The file contains the plasmid name, its length in base pairs and the feature
table, including each feature's show/hide setting. Spaces in the plasmid name
are replaced with underscores. Open it again with **File → Open...**; see
:doc:`opening_files` and :doc:`../file_formats/csv_tsv` for the layout.

.. note::
   You do not need to click **Apply to Plasmid** first: the latest values in
   the table are saved. Saving the image does not save the table, and vice versa.

Summary
-------

.. list-table::
   :header-rows: 1
   :widths: 25 30 45

   * - Action
     - Where
     - File types
   * - Save the map image
     - **File → Save As...**
     - ``.png``, ``.svg``, ``.pdf``, ``.jpg``
   * - Save the feature data
     - **Save Data** button (Table tab)
     - ``.csv``, ``.tsv``
