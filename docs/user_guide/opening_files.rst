File Types
==========

Choose **File → Open** and select a file. PlasmidEasel accepts three formats.

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Format
     - Extension
     - Details
   * - CSV
     - ``.csv``
     - Comma-separated feature table. See :doc:`../file_formats/csv_tsv`.
   * - TSV
     - ``.tsv``
     - Tab-separated feature table. See :doc:`../file_formats/csv_tsv`.
   * - GenBank
     - ``.gb``
     - Standard GenBank record. See :doc:`../file_formats/genbank`.

CSV and TSV files
-----------------

A CSV or TSV file must start with two lines: the plasmid name and its length in
base pairs. A header row and one row per feature follow. The header row must
contain these columns:

``index``, ``name``, ``type``, ``start``, ``end``, ``direction``, ``colour``

An optional ``show`` column controls whether each feature is drawn.

Full details, column descriptions and examples are in :doc:`../file_formats/csv_tsv`.

GenBank files
-------------

The plasmid name, length and features are read from the file automatically.
See :doc:`../file_formats/genbank` for how GenBank fields map to the feature
table.
