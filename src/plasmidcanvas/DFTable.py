import tkinter as tk
import ttkbootstrap as ttk
import pandas as pd
from ttkbootstrap.constants import *
from ttkbootstrap.validation import *


def columnTypeToVariable(var_type, value):
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
    if col_type == 'String':
        add_text_validation(entry, when='key')
    elif col_type == 'Int':
        add_numeric_validation(entry, when='key')
    elif col_type == 'Float':
        add_numeric_validation(entry, when='key')
    else:
        add_text_validation(entry, when='key')


class DFTable(ttk.Frame):
    def __init__(self, master=None, df=None, col_types=[]):
        super().__init__(master)
        self.master = master
        self.df: pd.DataFrame = df
        self.table_df: pd.DataFrame = self.df.copy()
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
        self.df = self.table_df.applymap(lambda x: x.get())
        return self.df

    def update_index(self, init=False):
        if not init:
            [x.set(i+1) for i, x in zip(range(self.table_df.shape[0]), self.table_df['index'])]
            for row, i in zip(self.rows, range(len(self.rows))):
                row.row = i
        self.table_df.rename({'index':'index_vars'}, axis=1, inplace=True)
        self.table_df.reset_index(inplace=True, drop=True)
        self.table_df.rename({'index_vars':'index'}, axis=1, inplace=True)

    def delete_row(self, ind, label, index_1=True):
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

    def undo_delete_row(self, ind=None, label=None, row=None, table=None):
        # if ind and label not provided undo most recent delete
        if table is None and row is None:
            if ind is None:
                command = self.deleted_rows[-1]

            else:
                command = [x for x in self.deleted_rows if x[1] == label and x[0] == ind][0]
            row = command[2]
            table = command[3]
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
        # First update grid position for all rows to ensure sensible grid indexing
        self.update_index()
        self.grid_row_alignment()
        # Add row with blank values to table and table_df
        new_row = DFRow(self, len(self.rows), init=False)
        self.rows.append(new_row)
        self.update_index()

    def grid_row_alignment(self):
        # For row in rows enforce grid position to match list index + 1
        for row in self.rows:
            row.row = self.rows.index(row)
            for entry in row.entries:
                entry.grid(row=row.row + 1, column=row.entries.index(entry), sticky=W, padx=5, pady=5)


class DFRow(ttk.Frame):
    def __init__(self, master: DFTable = None, row_index: int = None, init=True):
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
                var = columnTypeToVariable(col_type, master.df.iloc[self.row][i])
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
            master.table_df.iloc[self.row, i] = var

    # create update function for row, update df from string vars
    def update_row(self):
        if self.row == self.master.df.shape[0]:
            self.master.df.loc[self.row] = self.master.df.loc[self.row - 1]
        for i in range(len(self.master.df.columns)):
            self.master.df.iat[self.row, i] = self.master.table_df.iloc[self.row][i].get()
