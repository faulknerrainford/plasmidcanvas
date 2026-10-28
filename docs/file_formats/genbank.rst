GenBank files
=============

PlasmidEasel opens single-record GenBank files with the ``.gb`` extension.

How a file is read
------------------

* **Title:** the LOCUS name of the record.
* **Length:** the length of the sequence in base pairs.
* **Features:** every feature in the file becomes a row in the feature table.

For each feature:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Table column
     - Taken from
   * - ``name``
     - The first of the ``label``, ``product`` or ``gene`` qualifiers that is
       present. If none exist, the feature type is used.
   * - ``type``
     - The feature key, for example ``CDS`` or ``promoter``.
   * - ``start`` / ``end``
     - The feature location.
   * - ``direction``
     - The strand: ``1`` forward, ``-1`` reverse, ``0`` if no strand is given.
   * - ``colour``
     - Any qualifier containing ``color`` or ``colour`` (for example
       ``/ApEinfo_fwdcolor``). Defaults to ``black``.

Notes
-----

* Only one record per file is supported.
* After opening, features can be edited like those from a CSV or TSV file. See
  :doc:`csv_tsv` for the table columns.
