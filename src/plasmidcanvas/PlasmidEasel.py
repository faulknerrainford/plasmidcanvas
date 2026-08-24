import tkinter as tk
from tkinter import filedialog
import ttkbootstrap as ttk
import pandas as pd
from ttkbootstrap.constants import *
from ttkbootstrap.icons import Emoji
from ttkbootstrap.validation import *
from plasmidcanvas import Plasmid, draw_plasmid
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
from functools import partial
from Bio import SeqIO
from plasmidcanvas.DFTable import DFTable

class PlasmidEasel(ttk.Window):
    """
    Main application window for the PlasmidEasel GUI.

    Extends ``ttkbootstrap.Window`` and provides a matplotlib canvas for
    plasmid visualisation alongside tabbed control panels for editing plasmid
    properties and feature tables.

    Attributes
    ----------
    plasmid_title : tk.StringVar
        The current plasmid name.
    plasmid_bps : tk.IntVar
        The current plasmid length in base pairs.
    PLASMID : Plasmid
        The Plasmid model object being visualised.
    PLASMID_DF : pd.DataFrame or None
        Feature data loaded from file.
    FIG : matplotlib.figure.Figure
        The active figure used for rendering.
    fig_size : tuple of int
        Width and height in inches for the matplotlib figure.
    canvas_figures : list of FigureCanvasTkAgg
        History of canvas objects; the last entry is the active one.
    plasmid_style : tk.StringVar
        Selected rendering style (``'default'`` or ``'minimalist'``).
    commands_log : list
        Command history for undo/redo, capped at 10 entries.
    commands_pointer : int
        Index into ``commands_log`` pointing to the current state.
    """

    def __init__(self, **kw):
        """
        Initialise the window, menus, matplotlib canvas and control panels.

        Parameters
        ----------
        **kw
            Keyword arguments forwarded to ``ttkbootstrap.Window``.
        """
        super(PlasmidEasel, self).__init__(themename="pulse", **kw)
        self.title("PlasmidEasel")
        self.plasmid_title = tk.StringVar(None, "TORC")
        self.plasmid_bps = tk.IntVar(None, 1200)
        self.PLASMID: Plasmid = Plasmid(self.plasmid_title.get(), self.plasmid_bps.get())
        self.PLASMID_DF: pd.DataFrame = pd.DataFrame()
        self.SEPARATORS = {"tsv": "\t", "csv": ","}
        self.FIG = self.PLASMID.plot()
        self.fig_size = (3, 3)
        self.FIG.set_size_inches(self.fig_size[0], self.fig_size[1])
        self.canvas_figures = []
        self.plasmid_style = tk.StringVar(None, 'default')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.commands_log: list[tuple] = [()]
        self.commands_pointer = 0

        # Creating Menubar
        menubar = tk.Menu(self)

        # Adding File Menu and commands
        file = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='File', menu=file)
        file.add_command(label='Open...', command=self.open_file)
        file.add_command(label='Save As...', command=self.save_canvas)
        file.add_separator()
        file.add_command(label='Exit', command=self.destroy)

        # Adding Edit Menu and commands
        self.edit = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Edit', menu=self.edit)

        self.edit.add_command(label='Undo', command=self.undo_command, accelerator='Ctrl+Z', state='disabled')
        self.edit.add_command(label='Redo', command=self.redo_command, accelerator='Ctrl+Shift+Z', state='disabled')
        self.bind('<Control-z>', self.undo_command, add='+')
        self.bind('<Control-Shift-z>', self.redo_command, add='+')


        # Adding Help Menu
        help_ = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Help', menu=help_)
        # help_.add_command(label='PlasmidEasel Docs', command=None, state='disabled')

        self.config(menu=menubar)

        # Add canvas to draw figure on
        CANVAS = FigureCanvasTkAgg(self.FIG, master=self)
        self.canvas_figures.append(CANVAS)
        CANVAS.draw()
        CANVAS.get_tk_widget().grid(row=0, column=0, sticky='nsew')

        # Add notebook for control pannels
        controlpannels = ttk.Notebook(self, bootstyle="secondary")
        general = GeneralPanel(controlpannels)
        self.table = TablePanel(controlpannels)
        controlpannels.add(general, text="General")
        controlpannels.add(self.table, text="Table")
        controlpannels.grid(row=0, column=1, sticky='nsew')
        controlpannels.columnconfigure(0, weight=1)
        controlpannels.rowconfigure(0, weight=1)

    def open_file(self):
        """
        Open a CSV, TSV or GenBank file and load its contents.

        Prompts the user with a file dialog. On success the plasmid title,
        base-pair count and feature DataFrame are updated, the table panel is
        reloaded and the plasmid canvas is redrawn.
        """
        filename = filedialog.askopenfilename(defaultextension='.csv',
                                              filetypes=[('CSV files', '*.csv'), ('TSV Files', '*.tsv'), ('Genbank', '*.gb')])
        if filename.endswith('.csv') or filename.endswith('.tsv'):
            file = open(filename, mode='r')
            contents = file.readlines()
            self.plasmid_bps.set(int(contents[1]))
            self.plasmid_title.set(contents[0].split()[0])
            # HEADER = contents[0].split()[1:]
            self.PLASMID_DF = pd.read_csv(filename, sep=self.SEPARATORS[filename[-3:]], header=2)
        elif filename.endswith('.gb'):
            # load genbank file and convert to plasmid df
            sequence = SeqIO.read(filename, 'genbank')
            # Get plasmid label and bp_length
            self.plasmid_title.set(sequence.name)
            self.plasmid_bps.set(len(sequence.seq))
            # Set up dataframe to take features
            plasmid_df = pd.DataFrame(columns=["index", "name",	"type",	"start", "end",	"direction", "colour"])
            i = 0
            for feature in sequence.features:
                # For each feature get: name, type, start, end, direction and colour
                name = feature.qualifiers['label'][0]
                type = feature.type
                start = feature.location.start
                end = feature.location.end
                direction = feature.strand
                colour = 'black'
                for col in feature.qualifiers.keys():
                    if "color" in col:
                        colour = feature.qualifiers[col][0]
                # form row and add to dataframe
                plasmid_df.loc[len(plasmid_df)] = [i, name, type, start, end, direction, colour]
                i += 1
            self.PLASMID_DF = plasmid_df

        self.table.load_data()
        self.PLASMID = draw_plasmid(self.PLASMID_DF, self.plasmid_title.get(), self.plasmid_bps.get(),
                                    self.plasmid_style.get())
        self.redraw_plasmid()

    def save_canvas(self):
        """
        Save the current plasmid figure to a user-chosen file.

        Supports PNG, SVG, PDF and JPG output formats selected via a save
        dialog.
        """
        filename = filedialog.asksaveasfilename(filetypes=[('PNG files', '*.png'), ('SVG files', '*.svg'),
                                                           ('PDF files', '*.pdf'), ('JPG files', '*.jpg')])
        self.PLASMID.save_to_file(filename)

    def redraw_plasmid(self):
        """
        Replace the active matplotlib canvas with a freshly drawn figure.

        Removes the previous canvas from the grid and places the new one in
        its position.
        """
        self.FIG = self.PLASMID.plot()
        self.FIG.set_size_inches(self.fig_size[0], self.fig_size[1])
        self.canvas_figures[-1].get_tk_widget().pack_forget()
        new_canvas = FigureCanvasTkAgg(self.FIG, master=self)
        self.canvas_figures.append(new_canvas)
        new_canvas.draw_idle()
        new_canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')

    def update_plasmid(self, *kw):
        """
        Record a command snapshot and regenerate the plasmid from current settings.

        Logs the current state to the undo history, rebuilds ``self.PLASMID``
        via ``draw_plasmid`` and triggers a canvas redraw.

        Parameters
        ----------
        *kw
            Unused; present so the method can be used as a tkinter callback.
        """
        self.command_add(("GENERAL_PLASMID_UPDATE", self.PLASMID, self.plasmid_title.get(), self.plasmid_bps.get()))
        self.PLASMID = draw_plasmid(self.PLASMID_DF, self.plasmid_title.get(), self.plasmid_bps.get(),
                                    self.plasmid_style.get())
        self.redraw_plasmid()
        self.focus_get().focus_set()

    def command_add(self, command: tuple):
        """
        Append a command tuple to the undo/redo history.

        Truncates any redo-forward history beyond the current pointer, appends
        the new command, and keeps the log to at most 10 entries. Enables the
        Undo menu item and disables Redo.

        Parameters
        ----------
        command : tuple
            A descriptor whose first element is the command name string, e.g.
            ``'GENERAL_PLASMID_UPDATE'``, ``'DELETE'``, or ``'ADD_ROW'``.
        """
        self.commands_pointer += 1
        if self.commands_pointer != len(self.commands_log)-1:
            self.commands_log= self.commands_log[:self.commands_pointer]
        self.commands_log.append(command)
        if len(self.commands_log) > 11:
            self.commands_pointer = 10
            self.commands_log.remove(self.commands_log[1])
        self.edit.entryconfig('Undo', state=tk.NORMAL)
        self.edit.entryconfig('Redo', state=tk.DISABLED)

    def undo_command(self, *kw):
        """
        Undo the most recent logged command.

        Restores the application state described by the command at
        ``commands_pointer`` and decrements the pointer. Disables Undo when
        the beginning of the log is reached and enables Redo.
        """
        if self.commands_log[self.commands_pointer][0]:
            command = self.commands_log[self.commands_pointer]
            if command[0] == "GENERAL_PLASMID_UPDATE":
                self.PLASMID = command[1]
                self.redraw_plasmid()
                self.focus_get().focus_set()
            elif command[0] == "DELETE":
                self.table.RowPanel.undo_delete_row(command[1], command[2], command[3], command[4])
            elif command[0] == "ADD_ROW":
                ind = self.table.Table.table_df.shape[0] - 1
                self.table.RowPanel.delete_row(ind, log=False)
            self.commands_pointer -= 1
        self.edit.entryconfig('Redo', state=tk.NORMAL)
        if self.commands_pointer == 0:
            self.edit.entryconfig('Undo', state=tk.DISABLED)

    def redo_command(self, *kw):
        """
        Redo the next command in the history log.

        Advances ``commands_pointer`` and re-applies the command at the new
        position. Disables Redo when the end of the log is reached.
        """
        if len(self.commands_log) > self.commands_pointer + 1:
            self.commands_pointer += 1
            if len(self.commands_log)-1 == self.commands_pointer:
                self.edit.entryconfig('Redo', state=tk.DISABLED)
            command = self.commands_log[self.commands_pointer]
            if command[0] == "GENERAL_PLASMID_UPDATE":
                self.plasmid_title.set(command[2])
                self.plasmid_bps.set(command[3])
                self.PLASMID = draw_plasmid(self.PLASMID_DF, self.plasmid_title.get(), self.plasmid_bps.get(),
                                            self.plasmid_style.get())
                self.redraw_plasmid()
                self.focus_get().focus_set()
            elif command[0] == "DELETE":
                self.table.RowPanel.delete_row(command[1], log=False)
                pass
            elif command[0] == "ADD_ROW":
                self.table.add_row(log=False)


class GeneralPanel(ttk.Frame):
    """
    A control panel for editing high-level plasmid properties.

    Provides style-selection radio buttons, plasmid title and base-pair-size
    inputs, and an Apply button. All controls are bound to the parent
    ``PlasmidEasel`` instance.

    Parameters
    ----------
    master : tk.Widget, optional
        The parent notebook or container widget.
    """

    def __init__(self, master=None):
        """
        Build and lay out the style selector, title/BP inputs and Apply button.

        Parameters
        ----------
        master : tk.Widget, optional
            The parent widget (typically a ``ttk.Notebook``).
        """
        super().__init__(master)
        self.Easel = self.master.master
        # Radio button style selection
        style = tk.LabelFrame(self, text='Style')

        style_default = ttk.Radiobutton(style, text='Default', variable=self.Easel.plasmid_style, value='default',
                                        command=self.Easel.update_plasmid)
        style_mini = ttk.Radiobutton(style, text='Minimalist', variable=self.Easel.plasmid_style, value='minimalist',
                                     command=self.Easel.update_plasmid)
        style_default.grid(row=0, column=0, sticky='nsew', pady=5, padx=5)
        style_mini.grid(row=0, column=1, sticky='nsew', pady=5, padx=5)

        style.grid(row=0, column=0, sticky='nsew', pady=5, padx=5, columnspan=2)

        # Title label with textinput, preset to match plasmid_title and updates when modified
        title_label = ttk.Label(self, text='Plasmid Title', font=('Arial', 12))
        title_label.grid(row=1, column=0, sticky='nsew', pady=5, padx=5)
        self.title_input = ttk.Entry(self, textvariable=self.Easel.plasmid_title)
        self.title_input.grid(row=1, column=1, sticky='nsew', pady=5, padx=5)
        # Same as above with bp size
        bps_label = ttk.Label(self, text='Base Pair Size', font=('Arial', 12))
        bps_label.grid(row=2, column=0, sticky='nsew', pady=5, padx=5)
        self.bps_input = ttk.Entry(self, textvariable=self.Easel.plasmid_bps)
        add_numeric_validation(self.bps_input, when='key')
        self.bps_input.grid(row=2, column=1, sticky='nsew', pady=5, padx=5)
        # Update plasmid with new labels
        apply = ttk.Button(self, command=self.Easel.update_plasmid, text='Apply')
        apply.grid(row=3, column=0, sticky='nsew', pady=5, padx=5)

class TablePanel(ttk.Frame):
    """
    A control panel providing the editable feature table and row-management controls.

    Hosts a ``DFTable``, a ``RowPanel`` for per-row deletion, and buttons for
    adding rows, deleting rows by name, undoing deletions, applying changes to
    the plasmid and saving data.

    Parameters
    ----------
    master : ttk.Notebook, optional
        The parent notebook widget.

    Attributes
    ----------
    Easel : PlasmidEasel
        Reference to the top-level application window.
    Table : DFTable or None
        The active editable table widget; None until ``load_data`` is called.
    delete_var : tk.StringVar or None
        Holds the currently selected delete-target string.
    undo_delete_button : ttk.Button or None
        Enabled when deletions are available to undo.
    delete_select : ttk.Combobox or None
        Lists rows available for deletion by index and name.
    """

    def __init__(self, master: ttk.Notebook =None):
        """
        Initialise the panel with empty attribute placeholders.

        Parameters
        ----------
        master : ttk.Notebook, optional
            The parent notebook widget.
        """
        super().__init__(master)
        self.Easel: PlasmidEasel | Misc | None = self.master.master
        self.Table: DFTable | None = None
        self.delete_var: tk.StringVar | None = None
        self.undo_delete_button: ttk.Button | None = None
        self.delete_select: ttk.Combobox | None = None

    def load_data(self):
        """
        Build the DFTable and all row-management controls from ``Easel.PLASMID_DF``.

        Replaces any existing table with a freshly constructed ``DFTable`` and
        ``RowPanel``, then lays out Apply, Add Row, Save Data and Delete controls.
        """
        if self.Table:
            self.Table.grid_forget()
        self.Table = DFTable(self, self.Easel.PLASMID_DF,
                             ['Int', 'String', 'String', 'Int', 'Int', 'Int', 'String'])
        self.Table.grid(row=0, column=0, sticky='nsew', pady=5, padx=5, columnspan=4)
        self.RowPanel = RowPanel(self)
        self.RowPanel.grid(row=0, column=4, sticky='ew', pady=5, padx=5)
        # Add buttons for save data, add row, delete row and undo delete
        apply_button = ttk.Button(self, text='Apply to Plasmid', command=self.apply_to_plasmid)
        apply_button.grid(row=1, column=0, sticky='nsew', pady=5, padx=5)
        add_button = ttk.Button(self, text='Add Row', command=self.add_row)
        add_button.grid(row=1, column=1, sticky='nsew', pady=5, padx=5)
        save_button = ttk.Button(self, text='Save Data', command=self.save_data)
        save_button.grid(row=1, column=2, sticky='nsew', pady=5, padx=5)
        self.delete_var = ttk.StringVar()
        delete_frame = ttk.Labelframe(self, text='Delete', bootstyle='info')
        delete_frame.grid(row=1, column=3, sticky='nsew', pady=5, padx=5, columnspan=1)
        delete_button = ttk.Button(delete_frame, text='Delete Row', command=self.delete_row)
        delete_button.grid(row=0, column=0, sticky='nsew', pady=5, padx=5)
        self.undo_delete_button = ttk.Button(delete_frame, text='Undo Delete', command=self.undo_delete, state=tk.DISABLED)
        self.undo_delete_button.grid(row=1, column=0, sticky='nsew', pady=5, padx=5)
        self.delete_select = ttk.Combobox(delete_frame, textvariable=self.delete_var, bootstyle='info')
        self.delete_select['values']= tuple([str(ind.get())+'. '+label.get() for ind, label in zip(self.Table.table_df['index'],self.Table.table_df['name'])])
        self.delete_select.grid(row=0, column=1, sticky='nsew', pady=5, padx=5)

    def add_row(self, log=True):
        """
        Append a blank row to the table and refresh the delete combobox.

        Parameters
        ----------
        log : bool, optional
            If ``True`` (default), records the operation in the undo history.
        """
        self.Table.add_row()
        self.RowPanel.add_row()
        self.delete_select['values']= tuple([str(ind.get())+'. '+label.get() for ind, label in zip(self.Table.table_df['index'],self.Table.table_df['name'])])
        if log:
            self.master.Easel.command_add(("ADD_ROW"))

    def delete_row(self, log=True):
        """
        Delete the row currently selected in the delete combobox.

        Parameters
        ----------
        log : bool, optional
            If ``True`` (default), records the operation in the undo history.
        """
        ind, label = self.delete_var.get().split('. ')
        ind = int(ind)
        command = ("DELETE", ind, label, self.Table.rows.copy(), self.Table.table_df.copy())
        if log:
            self.Easel.command_add(command)
        self.Table.delete_row(ind, label)
        self.undo_delete_button.config(state=tk.NORMAL)
        self.delete_select['values']= tuple([str(ind.get())+'. '+label.get() for ind, label in zip(self.Table.table_df['index'],self.Table.table_df['name'])])

    def undo_delete(self, index=None, label=None):
        """
        Restore the most recent (or specified) deleted row.

        Parameters
        ----------
        index : int, optional
            0-based index of the row to restore.
        label : str, optional
            ``'name'`` column value of the row to restore.
        """
        self.Table.undo_delete_row(index, label)
        self.delete_select['values']= tuple([str(ind.get())+'. '+label.get() for ind, label in zip(self.Table.table_df['index'],self.Table.table_df['name'])])
        if len(self.Table.deleted_rows) == 0:
            self.undo_delete_button.config(state=tk.DISABLED)

    def apply_to_plasmid(self):
        """
        Flush table edits to the plasmid model and trigger a redraw.

        Calls ``update_table`` on the ``DFTable``, updates ``Easel.PLASMID_DF``,
        invokes ``update_plasmid``, and resets the undo-delete button state.
        """
        self.Easel.PLASMID_DF = self.Table.update_table()
        self.Easel.update_plasmid()
        self.undo_delete_button.config(state=tk.DISABLED)
        self.delete_select['values']= tuple([str(ind.get())+'. '+label.get() for ind, label in zip(self.Table.table_df['index'],self.Table.table_df['name'])])

    def save_data(self):
        """
        Save the current table data to a file.

        .. note::
            Not yet implemented.
        """
        pass


class RowPanel(ttk.Frame):
    """
    A panel that renders a column of delete buttons aligned with table rows.

    One wastebasket button is shown per row in the associated ``DFTable``.
    Clicking a button deletes the corresponding row and updates the undo log.

    Parameters
    ----------
    master : TablePanel, optional
        The parent ``TablePanel`` widget.

    Attributes
    ----------
    Table : DFTable
        Reference to the sibling ``DFTable`` widget.
    buttons : list of ttk.Button
        Delete buttons, one per row.
    delete_icon : str
        Unicode wastebasket emoji used as the button label.
    """

    def __init__(self, master: TablePanel =None):
        """
        Construct the delete-button column, one button per existing table row.

        Parameters
        ----------
        master : TablePanel, optional
            The parent widget, expected to expose a ``Table`` attribute of
            type ``DFTable``.
        """
        super().__init__(master)
        self.Table: DFTable = self.master.Table
        if len(self.Table.table_df.columns) % 2:
            bootstyle = 'info-inverse'
        else:
            bootstyle = 'info'
        label = ttk.Label(self, text='delete?', bootstyle=bootstyle)
        label.grid(row=0, column=0, sticky='nsew', pady=5, padx=5)
        row_count = self.Table.table_df.shape[0]
        self.buttons = []
        self.delete_icon = Emoji.get("wastebasket")
        for i in range(row_count):
            delete_by_index = partial(self.delete_row, i)
            button = ttk.Button(self, text=self.delete_icon, bootstyle=(INFO, OUTLINE),
                                command=delete_by_index)
            button.grid(row=i+1, column=0, sticky='nsew', pady=4, padx=5)
            self.buttons.append(button)

    def delete_row(self, index, log=True):
        """
        Delete the table row at *index* and optionally log the operation.

        Parameters
        ----------
        index : int
            0-based index of the row to delete.
        log : bool, optional
            If ``True`` (default), records the operation in the undo history.
        """
        row_name = self.Table.table_df.iloc[index]["name"].get()
        command = ("DELETE", index, row_name, self.Table.rows.copy(), self.Table.table_df.copy())
        row_count = self.Table.table_df.shape[0]
        self.master.Table.delete_row(index+1, row_name)
        self.buttons[row_count-1].grid_forget()
        if log:
            self.master.Easel.command_add(command)

    def undo_delete_row(self, index, label, row=None, table=None):
        """
        Restore a previously deleted row and refresh the button column.

        Parameters
        ----------
        index : int
            0-based index of the row to restore.
        label : str
            ``'name'`` column value used to identify the target row.
        row : list, optional
            Row-list snapshot forwarded to ``DFTable.undo_delete_row``.
        table : pd.DataFrame, optional
            Table snapshot forwarded to ``DFTable.undo_delete_row``.
        """
        self.Table.undo_delete_row(index, label, row, table)
        self.add_row()

    def add_row(self):
        """
        Show or create a delete button for a newly added table row.

        If a previously hidden button exists it is re-gridded at the correct
        position; otherwise a new button is created and appended to
        ``self.buttons``.
        """
        row_count = self.Table.table_df.shape[0]
        if len(self.buttons) >= row_count:
            self.buttons[row_count-1].grid(row=row_count, column=0, sticky='nsew', pady=4, padx=5)
        else:
            button = ttk.Button(self, text=self.delete_icon, bootstyle=(INFO, OUTLINE),
                                command=lambda: self.delete_row(row_count))
            button.grid(row=row_count, column=0, sticky='nsew', pady=4, padx=5)
            self.buttons.append(button)


if __name__ == '__main__':
    easel = PlasmidEasel()
    easel.mainloop()
