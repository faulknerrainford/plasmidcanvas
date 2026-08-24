import tkinter as tk
import ttkbootstrap as ttk
import pandas as pd
from ttkbootstrap.constants import *
from ttkbootstrap.validation import *


def columnTypeToVariable(var_type, value):
    """
    Convert a column type string to the appropriate tkinter variable.

    Parameters
    ----------
    var_type : str
        The column type. One of ``'String'``, ``'Int'``, ``'Float'``,
        ``'Boolean'``. Unrecognised values fall back to ``StringVar``.
    value : any
        The initial value assigned to the variable.

    Returns
    -------
    tk.Variable
        A tkinter variable of the corresponding type (``StringVar``,
        ``IntVar``, ``DoubleVar``, or ``BooleanVar``).
    """
    if var_type == 'String':
        return tk.StringVar(None, value)
    elif var_type == 'Int':
        return tk.IntVar(None, value)
    elif var_type == 'Float':
        return tk.DoubleVar(None, value)
    elif var_type == 'Boolean':
        return tk.BooleanVar(None, value)
    else:
        return tk.StringVar(None, value)


def add_validation(entry, col_type):
    """
    Add keystroke-level input validation to a tkinter Entry widget.

    Parameters
    ----------
    entry : ttk.Entry
        The entry widget to validate.
    col_type : str
        The column type. ``'Int'`` and ``'Float'`` receive numeric validation;
        all other values (including ``'String'``) receive text validation.
    """
    if col_type == 'String':
        add_text_validation(entry, when='key')
    elif col_type == 'Int':
        add_numeric_validation(entry, when='key')
    elif col_type == 'Float':
        add_numeric_validation(entry, when='key')
    else:
        add_text_validation(entry, when='key')


class DFTable(ttk.Frame):
    """
    A tkinter Frame that renders a pandas DataFrame as an editable grid.

    Each cell is backed by a tkinter variable so values can be harvested back
    as a DataFrame via `update_table`.

    Parameters
    ----------
    master : tk.Widget, optional
        The parent widget.
    df : pd.DataFrame, optional
        The DataFrame whose contents populate the table.
    col_types : list of str, optional
        Per-column type strings (``'String'``, ``'Int'``, ``'Float'``,
        ``'Boolean'``) controlling the variable type and input validation.

    Attributes
    ----------
    df : pd.DataFrame
        The original source DataFrame.
    table_df : pd.DataFrame
        Same shape as *df*; cells hold tkinter variables instead of raw values.
    rows : list of DFRow
        Currently displayed row objects.
    column_types : list of str
        The column-type strings supplied at construction.
    deleted_rows : list of tuple
        Stack of deleted-row snapshots used for undo operations.
    """

    def __init__(self, master=None, df=None, col_types=None):
        """
        Initialise the DFTable and render column headers and rows.

        Parameters
        ----------
        master : tk.Widget, optional
            The parent widget.
        df : pd.DataFrame, optional
            The DataFrame to display.
        col_types : list of str, optional
            Per-column type strings for variable creation and validation.
        """
        super().__init__(master)
        if col_types is None:
            col_types = []
        self.master = master
        self.df: pd.DataFrame = df
        self.table_df: pd.DataFrame | None = pd.DataFrame(None, index=self.df.index, columns=self.df.columns)
        self.rows = []
        self.column_types = col_types
        self.deleted_rows = []
        if 'index' not in self.df.columns:
            self.update_index(init=True)

        # Set up headers
        grid_col = 0
        for header in df.columns:
            if grid_col % 2 == 0:
                bootstyle = 'info-inverse'
            else:
                bootstyle = 'info'
            label = ttk.Label(master=self, text=header, bootstyle=bootstyle)
            label.grid(row=0, column=grid_col, padx=5, pady=5, sticky='nsew')
            grid_col += 1

        # for each row generate row object and pack
        for i in range(self.df.shape[0]):
            row = DFRow(self, i)
            self.rows.append(row)

    # update function for table, updates all rows
    def update_table(self) -> pd.DataFrame:
        """
        Collect current cell values and return an updated DataFrame.

        Resets the index column then applies all tkinter variable values back
        into ``self.df``.

        Returns
        -------
        pd.DataFrame
            The updated DataFrame with current widget values.
        """
        # # TODO: Modify to just generate a new df of values from table df
        # # check for deleted rows
        # if len(self.deleted_rows) > 0:
        #     for row in self.deleted_rows:
        #         # check for label and ind match in df (if not undo delete and worry about the state of existence)
        #         if self.df.iloc[row[0]]['name'] == row[1]:
        #             # delete row from df
        #             self.df = self.df.drop(row[0])
        #         # clear deleted rows list
        #         self.deleted_rows.remove(row)
        # for row in self.rows:
        #     row.update_row()
        self.update_index()
        self.df = self.table_df.map(lambda x: x.get())
        return self.df

    def update_index(self, init=False):
        """
        Resequence the ``'index'`` column of ``table_df`` to reflect current row order.

        Parameters
        ----------
        init : bool, optional
            If ``True``, only resets the DataFrame integer index without
            updating the ``'index'`` column values or row positions.
            Default is ``False``.
        """
        if not init:
            [x.set(i+1) for i, x in zip(range(self.table_df.shape[0]), self.table_df['index'])]
            for row, i in zip(self.rows, range(len(self.rows))):
                row.row = i
        self.table_df.rename({'index':'index_vars'}, axis=1, inplace=True)
        self.table_df.reset_index(inplace=True, drop=True)
        self.table_df.rename({'index_vars':'index'}, axis=1, inplace=True)

    def delete_row(self, ind, label, index_1=True):
        """
        Remove a row from the table by index and label, saving a snapshot for undo.

        Parameters
        ----------
        ind : int
            Row index. When *index_1* is ``True`` this is 1-based.
        label : str
            Value of the ``'name'`` column for the target row, used to confirm
            identity before deletion.
        index_1 : bool, optional
            If ``True`` (default), convert *ind* from 1-based to 0-based
            internally.
        """
        if index_1:
            ind = ind - 1
        # check label matches for index in table_df
        if self.table_df.iloc[ind]['name'].get() == label and self.rows[ind].row == ind:
            # identify row for entries and check index and label match
            row = self.rows[ind]
            # add (ind, label, row(from row list), vars(row from table_df)) to deleted rows
            self.deleted_rows.append((ind, label, self.rows.copy(), self.table_df.copy()))
            # grid remove entry widgets
            for entry in row.entries:
                entry.grid_remove()
            # delete row from rows list
            self.rows.remove(row)
            # delete row from table_df
            self.table_df = self.table_df.drop(ind)
        # update index
        self.update_index()

    def undo_delete_row(self, ind=None, label=None, row=None, table: pd.DataFrame =None):
        """
        Restore a previously deleted row.

        If *row* and *table* are not supplied, the most recent deletion is
        undone. When *ind* and *label* are provided the matching snapshot is
        targeted from the deleted-rows stack.

        Parameters
        ----------
        ind : int, optional
            0-based index of the row to restore. Used together with *label*.
        label : str, optional
            ``'name'`` column value of the row to restore.
        row : list of DFRow, optional
            Explicit row-list snapshot. Takes precedence over the stored stack.
        table : pd.DataFrame, optional
            Explicit ``table_df`` snapshot. Takes precedence over the stored
            stack.
        """
        # if ind and label not provided undo most recent delete
        if table is None and row is None:
            if ind is None:
                command = self.deleted_rows[-1]

            else:
                command = [x for x in self.deleted_rows if x[1] == label and x[0] == ind][0]
            row = command[2]
            table: pd.DataFrame = command[3]
        if row:
            # use concat to insert row of variables back into table_df
            self.table_df = table
            # reset row list
            self.rows = row
            # update all rows grid positions (function)
            self.update_index()
            self.grid_row_alignment()
        pass

    def add_row(self):
        """
        Append a new blank row to the table.

        Updates grid alignment and index column before and after adding the row.
        """
        # First update grid position for all rows to ensure sensible grid indexing
        self.update_index()
        self.grid_row_alignment()
        # Add row with blank values to table and table_df
        new_row = DFRow(self, len(self.rows), init=False)
        self.rows.append(new_row)
        self.update_index()

    def grid_row_alignment(self):
        """
        Re-grid all row entries so their positions match their list indices.

        Iterates over ``self.rows`` and places each entry widget at
        ``row_index + 1`` (row 0 is reserved for column headers).
        """
        # For row in rows enforce grid position to match list index + 1
        for row in self.rows:
            row.row = self.rows.index(row)
            for entry in row.entries:
                entry.grid(row=row.row + 1, column=row.entries.index(entry), sticky=W, padx=5, pady=5)


class DFRow(ttk.Frame):
    """
    A logical row within a DFTable that owns the tkinter variables and widgets
    for a single DataFrame row.

    Parameters
    ----------
    master : DFTable, optional
        The parent DFTable widget.
    row_index : int, optional
        0-based position of this row in the table.
    init : bool, optional
        If ``True`` (default), populate cells from existing DataFrame values.
        If ``False``, duplicate the preceding row's variable types for a new
        blank row.

    Attributes
    ----------
    row : int
        Current 0-based row position.
    variables : list of tk.Variable
        Tkinter variable objects for each cell in the row.
    entries : list of ttk.Widget
        Entry (or Label for the index column) widgets for each cell.
    """

    def __init__(self, master: DFTable, row_index: int, init=True):
        """
        Create variables and entry widgets for one DataFrame row.

        Parameters
        ----------
        master : DFTable, optional
            The parent DFTable.
        row_index : int, optional
            0-based index of this row.
        init : bool, optional
            If ``True``, values are taken from the DataFrame. If ``False``,
            a blank row is created by copying variable types from the
            preceding row. Default is ``True``.
        """
        super().__init__(master)
        self.master: DFTable = master
        self.row = row_index
        self.variables = []
        self.entries = []

        if not init:
            master.table_df.loc[self.row] = master.table_df.loc[self.row - 1]

        # create entry and variable for each item in row
        for i in range(len(master.df.columns)):
            if len(master.column_types) > 0:
                col_type = master.column_types[i]
            else:
                col_type = 'String'
            if init:
                var = columnTypeToVariable(col_type, master.df.iloc[self.row, i])
            elif master.df.columns[i] in ['colour', 'color']:
                var = columnTypeToVariable(col_type, 'grey')
            else:
                var = columnTypeToVariable(col_type, None)
            self.variables.append(var)
            if master.df.columns[i] == 'index':
                entry = ttk.Label(master, textvariable=var, bootstyle='secondary')
                self.entries.append(entry)
                self.entries[i].grid(row=self.row + 1, column=i, sticky='NSEW', padx=5, pady=5)
            else:
                entry = ttk.Entry(master, textvariable=var)
                add_validation(entry, col_type)
                self.entries.append(entry)
                self.entries[i].grid(row=self.row + 1, column=i, sticky=W, padx=5, pady=5)
            # Add row variables to variables df
            master.table_df.iat[self.row, i] = var # type: ignore[call-overload]

    # create update function for row, update df from string vars
    def update_row(self):
        """
        Write current variable values back into the source DataFrame.

        If this row is beyond the current DataFrame length a new row is
        created by duplicating the last existing row before writing.
        """
        if self.row == self.master.df.shape[0]:
            self.master.df.loc[self.row] = self.master.df.loc[self.row - 1]
        for i in range(len(self.master.df.columns)):
            self.master.df.iat[self.row, i] = self.master.table_df.iloc[self.row][i].get()
