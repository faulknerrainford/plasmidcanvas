CSV and TSV files
=================

CSV (comma-separated) and TSV (tab-separated) files describe a plasmid and its
features. The separator is chosen from the file extension: ``.csv`` uses commas
and ``.tsv`` uses tabs.

File layout
-----------

The file has two header lines, then a table with one feature per row:

.. list-table::
   :header-rows: 1
   :widths: 10 90

   * - Line
     - Content
   * - 1
     - The plasmid name. Only the first word is used as the title, so avoid
       spaces or put the name first.
   * - 2
     - The plasmid length in base pairs, as a whole number.
   * - 3
     - The column headers (see below).
   * - 4+
     - One feature per row.

Required columns
----------------

The column headers must be spelled exactly as shown (lower case).

.. list-table::
   :header-rows: 1
   :widths: 15 15 70

   * - Column
     - Content
     - Description
   * - ``index``
     - Integer
     - Row number of the feature, usually counting up from 1.
   * - ``name``
     - Text
     - Feature name, shown as its label on the map.
   * - ``type``
     - Text
     - Feature category, for example ``promoter``, ``resistance_gene`` or
       ``restriction_site``. Features of the same type can be styled together
       in the Features tab. Any text is accepted.
   * - ``start``
     - Integer
     - Start position in base pairs.
   * - ``end``
     - Integer
     - End position in base pairs.
   * - ``direction``
     - ``1``, ``-1`` or ``0``
     - ``1`` is forward, ``-1`` is reverse. ``0`` (no direction) is drawn as a
       plain rectangle rather than an arrow. Features shorter than 10 bp are
       also drawn as rectangles. For circular DNA ``1`` is clockwise and ``-1`` is anticlockwise.
   * - ``colour``
     - Text
     - Feature colour as a hex code (``#ff6600``) or a colour name (``black``).

Optional columns
----------------

``show``
   Whether the feature is drawn on the map. If the column is missing it is
   added automatically when the file is opened.

Example
-------

A TSV file (columns separated by tabs)::

   pTORC16
   6218
   index	name	type	start	end	direction	colour
   1	Ptet	promoter	5	45	1	#ff6600
   2	Pantitet	promoter	40	80	-1	#ff6600

The same file as a CSV::

   pTORC16
   6218
   index,name,type,start,end,direction,colour
   1,Ptet,promoter,5,45,1,#ff6600
   2,Pantitet,promoter,40,80,-1,#ff6600

Tips
----

* Overlapping features are allowed. Their labels are moved automatically to
  avoid collisions.
* Make sure the file is saved as plain text (not an Excel workbook) with the
  ``.csv`` or ``.tsv`` extension.
* Example files are available in ``src/tests`` in the repository.
